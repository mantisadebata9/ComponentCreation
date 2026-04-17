"""
Figma Design Reader - Fetches and parses Figma designs via API or file upload
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FigmaFrame:
    """Represents a single Figma frame"""
    name: str
    id: str
    children: List[Dict[str, Any]]
    width: float
    height: float
    x: float
    y: float
    background_color: Optional[str] = None
    properties: Dict[str, Any] = None


@dataclass
class FigmaDesign:
    """Complete Figma design structure"""
    project_name: str
    frames: List[FigmaFrame]
    colors: Dict[str, str]
    typography: Dict[str, Any]
    spacing_tokens: List[Dict[str, Any]]
    raw_data: Dict[str, Any]


class FigmaReader:
    """
    Reads Figma designs from:
    1. Figma API (via URL)
    2. Uploaded .fig files
    3. Exported JSON
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("FIGMA_API_KEY")
        self.base_url = "https://api.figma.com/v1"
        self.headers = {
            "X-Figma-Token": self.api_key
        } if self.api_key else {}

    def read_from_url(self, figma_url: str) -> FigmaDesign:
        """
        Fetch design from Figma URL
        URL format: https://www.figma.com/file/{FILE_KEY}/...
        """
        try:
            file_key = self._extract_file_key(figma_url)
            if not file_key:
                raise ValueError("Invalid Figma URL format")

            logger.info(f"Fetching Figma design: {file_key}")

            # Fetch file metadata
            response = requests.get(
                f"{self.base_url}/files/{file_key}",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            design = self._parse_figma_response(data)
            logger.info(f"Successfully read {len(design.frames)} frames")
            return design

        except requests.exceptions.RequestException as e:
            logger.error(f"Figma API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading Figma design: {e}")
            raise

    def read_from_file(self, file_path: str) -> FigmaDesign:
        """
        Parse uploaded .fig or exported JSON file
        """
        path = Path(file_path)

        if path.suffix == ".json":
            return self._parse_json_file(file_path)
        elif path.suffix == ".fig":
            return self._parse_fig_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    def _parse_json_file(self, file_path: str) -> FigmaDesign:
        """Parse exported Figma JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info("Parsing Figma JSON export")
            design = self._parse_figma_response(data)
            return design

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON file: {e}")
            raise

    def _parse_fig_file(self, file_path: str) -> FigmaDesign:
        """
        Parse .fig binary file
        .fig files are ZIP archives containing JSON
        """
        import zipfile

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # .fig files contain a document.json in the root
                if 'document.json' in zip_ref.namelist():
                    with zip_ref.open('document.json') as f:
                        data = json.load(f)
                        return self._parse_figma_response(data)
                else:
                    raise ValueError(".fig file does not contain document.json")

        except zipfile.BadZipFile:
            logger.error("Invalid .fig file format")
            raise
        except Exception as e:
            logger.error(f"Error parsing .fig file: {e}")
            raise

    def _parse_figma_response(self, data: Dict[str, Any]) -> FigmaDesign:
        """
        Parse Figma API response or exported JSON
        Extract frames, colors, typography, spacing
        """
        try:
            frames = []
            colors = {}
            typography = {}

            # Extract project name
            project_name = data.get('name', 'Untitled Project')

            # Parse document
            document = data.get('document', {})
            
            # Extract frames from pages
            pages = document.get('children', [])
            for page in pages:
                page_frames = self._extract_frames_from_page(page)
                frames.extend(page_frames)

            # Extract design tokens
            colors = self._extract_colors(data)
            typography = self._extract_typography(data)
            spacing = self._extract_spacing(data)

            design = FigmaDesign(
                project_name=project_name,
                frames=frames,
                colors=colors,
                typography=typography,
                spacing_tokens=spacing,
                raw_data=data
            )

            logger.info(f"Parsed design: {project_name}")
            logger.info(f"Found {len(frames)} frames")

            return design

        except Exception as e:
            logger.error(f"Error parsing Figma response: {e}")
            raise

    def _extract_frames_from_page(self, page: Dict[str, Any]) -> List[FigmaFrame]:
        """Recursively extract frames from page"""
        frames = []

        def traverse(node):
            if node.get('type') == 'FRAME':
                frame = FigmaFrame(
                    name=node.get('name', 'Untitled Frame'),
                    id=node.get('id', ''),
                    children=node.get('children', []),
                    width=node.get('absoluteBoundingBox', {}).get('width', 0),
                    height=node.get('absoluteBoundingBox', {}).get('height', 0),
                    x=node.get('absoluteBoundingBox', {}).get('x', 0),
                    y=node.get('absoluteBoundingBox', {}).get('y', 0),
                    background_color=self._extract_fill_color(node),
                    properties=node
                )
                frames.append(frame)

            # Traverse children
            for child in node.get('children', []):
                traverse(child)

        traverse(page)
        return frames

    def _extract_fill_color(self, node: Dict[str, Any]) -> Optional[str]:
        """Extract fill color from node"""
        fills = node.get('fills', [])
        if fills and fills[0].get('visible', True):
            color = fills[0].get('color', {})
            r = int(color.get('r', 1) * 255)
            g = int(color.get('g', 1) * 255)
            b = int(color.get('b', 1) * 255)
            a = color.get('a', 1)
            return f"rgba({r}, {g}, {b}, {a})"
        return None

    def _extract_colors(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract color styles/variables"""
        colors = {}
        try:
            styles = data.get('styles', {})
            for style_id, style in styles.items():
                if style.get('styleType') == 'FILL':
                    colors[style.get('name', '')] = style.get('id', '')
        except Exception as e:
            logger.warning(f"Could not extract colors: {e}")
        return colors

    def _extract_typography(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract typography styles"""
        typography = {}
        try:
            styles = data.get('styles', {})
            for style_id, style in styles.items():
                if style.get('styleType') == 'TEXT':
                    typography[style.get('name', '')] = {
                        'id': style.get('id', ''),
                        'type': 'TEXT'
                    }
        except Exception as e:
            logger.warning(f"Could not extract typography: {e}")
        return typography

    def _extract_spacing(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract spacing tokens"""
        spacing = []
        try:
            # Common Figma spacing tokens
            standard_spacing = [8, 12, 16, 24, 32, 48, 64]
            for size in standard_spacing:
                spacing.append({
                    'name': f'spacing-{size}',
                    'value': size,
                    'unit': 'px'
                })
        except Exception as e:
            logger.warning(f"Could not extract spacing: {e}")
        return spacing

    @staticmethod
    def _extract_file_key(url: str) -> Optional[str]:
        """Extract Figma file key from URL"""
        try:
            # URL format: https://www.figma.com/file/{FILE_KEY}/...
            parts = url.split('/file/')
            if len(parts) > 1:
                file_key = parts[1].split('/')[0]
                return file_key
        except Exception as e:
            logger.error(f"Could not extract file key: {e}")
        return None