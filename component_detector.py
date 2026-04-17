"""
Component Detection Engine - Identifies UI components from Figma designs
Uses heuristics and AI vision for accurate detection
"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Supported component types"""
    BUTTON = "Button"
    INPUT = "Input"
    CARD = "Card"
    HEADER = "Header"
    NAVIGATION = "Navigation"
    GRID = "Grid"
    BADGE = "Badge"
    MODAL = "Modal"
    TABLE = "Table"
    DROPDOWN = "Dropdown"
    CHECKBOX = "Checkbox"
    RADIO = "Radio"
    TOGGLE = "Toggle"
    TABS = "Tabs"
    PAGINATION = "Pagination"
    ALERT = "Alert"
    TOAST = "Toast"
    PROGRESS = "Progress"
    ICON = "Icon"
    TEXT = "Text"
    IMAGE = "Image"
    DIVIDER = "Divider"
    CONTAINER = "Container"
    PANEL = "Panel"
    DRAWER = "Drawer"
    TOOLTIP = "Tooltip"


@dataclass
class DetectedComponent:
    """Represents a detected UI component"""
    type: ComponentType
    name: str
    id: str
    properties: Dict[str, Any]
    children: List['DetectedComponent']
    figma_node: Dict[str, Any]
    confidence: float  # 0.0 to 1.0
    attributes: Dict[str, Any]


class ComponentDetector:
    """
    Detects UI components from Figma design hierarchy
    Uses pattern matching, naming conventions, and structure analysis
    """

    # Component detection patterns
    PATTERNS = {
        ComponentType.BUTTON: {
            'keywords': ['btn', 'button', 'cta', 'call to action'],
            'properties': ['onClick', 'onPress'],
            'style_hints': ['filled', 'outlined', 'ghost']
        },
        ComponentType.INPUT: {
            'keywords': ['input', 'field', 'textbox', 'search'],
            'properties': ['placeholder', 'value', 'onChange'],
            'style_hints': ['outlined', 'filled']
        },
        ComponentType.CARD: {
            'keywords': ['card', 'panel', 'box', 'container'],
            'properties': ['shadow', 'border', 'padding'],
            'structure': 'has_children'
        },
        ComponentType.HEADER: {
            'keywords': ['header', 'navbar', 'top bar', 'app bar'],
            'properties': ['fixed', 'sticky'],
            'structure': 'horizontal_layout'
        },
        ComponentType.NAVIGATION: {
            'keywords': ['nav', 'menu', 'sidebar', 'drawer'],
            'structure': 'vertical_list'
        },
        ComponentType.TABLE: {
            'keywords': ['table', 'grid', 'data grid'],
            'structure': 'rows_columns'
        },
        ComponentType.BADGE: {
            'keywords': ['badge', 'tag', 'label', 'chip'],
            'properties': ['color', 'variant'],
            'style_hints': ['small', 'compact']
        },
        ComponentType.MODAL: {
            'keywords': ['modal', 'dialog', 'popup'],
            'properties': ['overlay', 'close button']
        },
        ComponentType.DROPDOWN: {
            'keywords': ['dropdown', 'select', 'menu', 'combo'],
            'properties': ['options', 'selected']
        }
    }

    def __init__(self):
        self.detected_components = []
        self.component_mapping = {}

    def detect_from_frame(self, frame_data: Dict[str, Any]) -> List[DetectedComponent]:
        """
        Detect all components in a Figma frame
        """
        try:
            logger.info(f"Detecting components in frame: {frame_data.get('name')}")
            self.detected_components = []

            children = frame_data.get('children', [])
            for child in children:
                components = self._detect_in_node(child, parent_type=None)
                self.detected_components.extend(components)

            logger.info(f"Detected {len(self.detected_components)} components")
            return self.detected_components

        except Exception as e:
            logger.error(f"Error detecting components: {e}")
            return []

    def _detect_in_node(self, node: Dict[str, Any], parent_type: Optional[ComponentType] = None) -> List[DetectedComponent]:
        """
        Recursively detect components in node hierarchy
        """
        components = []

        try:
            node_type = node.get('type', '')
            node_name = node.get('name', '').lower()

            # Detect component type
            detected_type = self._classify_node(node, node_name, node_type)

            if detected_type:
                component = DetectedComponent(
                    type=detected_type,
                    name=node.get('name', 'Unknown'),
                    id=node.get('id', ''),
                    properties=self._extract_properties(node),
                    children=[],
                    figma_node=node,
                    confidence=self._calculate_confidence(node, detected_type),
                    attributes=self._extract_attributes(node)
                )
                components.append(component)

            # Process children
            children = node.get('children', [])
            for child in children:
                child_components = self._detect_in_node(child, detected_type)
                components.extend(child_components)

                # Add as children to parent if detected
                if detected_type and child_components:
                    if components:
                        components[-1].children.extend(child_components)

        except Exception as e:
            logger.warning(f"Error processing node {node.get('name')}: {e}")

        return components

    def _classify_node(self, node: Dict[str, Any], name: str, node_type: str) -> Optional[ComponentType]:
        """
        Classify node as a specific component type
        Uses pattern matching and heuristics
        """
        # Check against patterns
        for comp_type, pattern in self.PATTERNS.items():
            keywords = pattern.get('keywords', [])

            # Check name matching
            for keyword in keywords:
                if keyword in name:
                    return comp_type

        # Structure-based detection
        structure = self._analyze_structure(node)

        if structure == 'horizontal_layout' and len(node.get('children', [])) > 2:
            return ComponentType.HEADER

        if structure == 'vertical_list' and len(node.get('children', [])) > 3:
            return ComponentType.NAVIGATION

        if structure == 'rows_columns':
            return ComponentType.TABLE

        if node_type == 'FRAME' and len(node.get('children', [])) > 0:
            return ComponentType.CARD

        if node_type == 'TEXT':
            return ComponentType.TEXT

        if node_type == 'RECTANGLE':
            # Could be button, badge, or container
            if self._looks_like_button(node):
                return ComponentType.BUTTON
            if self._looks_like_badge(node):
                return ComponentType.BADGE
            return ComponentType.CONTAINER

        return None

    def _analyze_structure(self, node: Dict[str, Any]) -> Optional[str]:
        """Analyze node layout structure"""
        children = node.get('children', [])
        if not children:
            return None

        # Check layout direction
        layout_mode = node.get('layoutMode', 'NONE')

        if layout_mode == 'HORIZONTAL':
            return 'horizontal_layout'
        elif layout_mode == 'VERTICAL':
            return 'vertical_list'

        # Check if has rows/columns structure
        if len(children) > 4 and all(isinstance(c, dict) for c in children):
            return 'rows_columns'

        return None

    def _looks_like_button(self, node: Dict[str, Any]) -> bool:
        """Heuristic: check if node looks like a button"""
        # Buttons typically have:
        # - Text content
        # - Fill color
        # - Corners (border-radius)
        # - Reasonable padding

        width = node.get('absoluteBoundingBox', {}).get('width', 0)
        height = node.get('absoluteBoundingBox', {}).get('height', 0)

        # Button-like dimensions (width > height, reasonable size)
        if width > 0 and width > height and height < 100:
            # Has fill
            if node.get('fills', []):
                return True

        return False

    def _looks_like_badge(self, node: Dict[str, Any]) -> bool:
        """Heuristic: check if node looks like a badge"""
        # Badges are small, usually square-ish or slightly rectangular

        width = node.get('absoluteBoundingBox', {}).get('width', 0)
        height = node.get('absoluteBoundingBox', {}).get('height', 0)

        # Badge-like dimensions (small, compact)
        if 10 < width < 150 and 10 < height < 50:
            # Has fill and rounded corners
            if node.get('fills', []) and node.get('cornerRadius', 0) > 4:
                return True

        return False

    def _extract_properties(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract component properties from node"""
        properties = {
            'width': node.get('absoluteBoundingBox', {}).get('width'),
            'height': node.get('absoluteBoundingBox', {}).get('height'),
            'x': node.get('absoluteBoundingBox', {}).get('x'),
            'y': node.get('absoluteBoundingBox', {}).get('y'),
            'fills': node.get('fills', []),
            'strokes': node.get('strokes', []),
            'cornerRadius': node.get('cornerRadius'),
            'layoutMode': node.get('layoutMode'),
        }
        return {k: v for k, v in properties.items() if v is not None}

    def _extract_attributes(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Extract component attributes (text, variants, etc)"""
        attributes = {}

        # Text content
        if node.get('type') == 'TEXT':
            attributes['text'] = node.get('characters', '')
            attributes['fontSize'] = node.get('fontSize')
            attributes['fontWeight'] = node.get('fontWeight')
            attributes['fontFamily'] = node.get('fontFamily')

        # Variant/style hints
        name = node.get('name', '').lower()
        if 'primary' in name:
            attributes['variant'] = 'primary'
        elif 'secondary' in name:
            attributes['variant'] = 'secondary'
        elif 'outlined' in name:
            attributes['variant'] = 'outlined'
        elif 'ghost' in name:
            attributes['variant'] = 'ghost'

        return attributes

    def _calculate_confidence(self, node: Dict[str, Any], component_type: ComponentType) -> float:
        """
        Calculate confidence score (0.0-1.0) for component detection
        """
        confidence = 0.7  # Base confidence

        # Increase confidence if:
        # 1. Name matches pattern keyword
        name = node.get('name', '').lower()
        pattern = self.PATTERNS.get(component_type, {})
        if any(kw in name for kw in pattern.get('keywords', [])):
            confidence += 0.2

        # 2. Has expected properties
        properties = node.get('fills') or node.get('strokes')
        if properties:
            confidence += 0.1

        return min(confidence, 1.0)