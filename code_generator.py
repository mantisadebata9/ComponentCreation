"""
Code Generator - Generates React TypeScript components from mapped Jutro components
"""
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from jinja2 import Template
import os

logger = logging.getLogger(__name__)


class CodeGenerator:
    """
    Generates React/TypeScript code from mapped Jutro components
    Creates:
    - Component files (.tsx)
    - Page layouts
    - Index files
    - Type definitions
    """

    COMPONENT_TEMPLATE = """import React from 'react';
import { {{ imports }} } from '@jutro/components';

interface {{ component_name }}Props {
  {{ props_interface }}
}

export const {{ component_name }}: React.FC<{{ component_name }}Props> = ({
  {{ props_destructure }}
}) => {
  return (
    {{ jsx_code }}
  );
};

export default {{ component_name }};
"""

    PAGE_TEMPLATE = """import React, { useState } from 'react';
import { Box } from '@jutro/components';
{{ component_imports }}

interface {{ page_name }}Props {
  data?: any;
}

export const {{ page_name }}: React.FC<{{ page_name }}Props> = ({ data }) => {
  {{ state_hooks }}

  return (
    <Box padding="24px">
      {{ page_layout }}
    </Box>
  );
};

export default {{ page_name }};
"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self._ensure_output_structure()

    def _ensure_output_structure(self):
        """Create output directory structure"""
        directories = [
            self.output_dir / "src" / "pages",
            self.output_dir / "src" / "components",
            self.output_dir / "src" / "types",
            self.output_dir / "src" / "layout",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def generate_components(self, mapped_components: List[Dict[str, Any]]) -> List[str]:
        """
        Generate component files from mapped components
        """
        generated_files = []

        try:
            for component in mapped_components:
                if component['confidence'] < 0.5:
                    logger.warning(f"Skipping low-confidence component: {component['figma_name']}")
                    continue

                file_path = self._generate_component_file(component)
                generated_files.append(str(file_path))

            logger.info(f"Generated {len(generated_files)} component files")
            return generated_files

        except Exception as e:
            logger.error(f"Error generating components: {e}")
            return []

    def generate_page(self, frame_name: str, components: List[Dict[str, Any]]) -> str:
        """
        Generate a page layout from frame components
        """
        try:
            page_name = self._sanitize_name(frame_name)
            component_imports = self._generate_imports(components)
            page_layout = self._generate_layout_jsx(components)
            state_hooks = self._generate_state_hooks(components)

            code = self.PAGE_TEMPLATE.format(
                page_name=page_name,
                component_imports=component_imports,
                page_layout=page_layout,
                state_hooks=state_hooks
            )

            # Write file
            file_path = self.output_dir / "src" / "pages" / f"{page_name}.tsx"
            file_path.write_text(code)

            logger.info(f"Generated page: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Error generating page: {e}")
            return ""

    def _generate_component_file(self, component: Dict[str, Any]) -> Path:
        """Generate a single component file"""
        component_name = self._sanitize_name(component['figma_name'])
        jutro_component = component['jutro_component']

        # Parse imports
        imports_list = component.get('import', '').split('\n')
        imports_str = ', '.join([imp.split('{')[1].split('}')[0].strip() for imp in imports_list if '{' in imp])

        # Generate props interface
        props = component.get('props', {})
        props_interface = self._generate_props_interface(props)
        props_destructure = ', '.join(props.keys()) if props else ''

        # Generate JSX
        jsx_code = self._generate_component_jsx(component)

        code = self.COMPONENT_TEMPLATE.format(
            imports=imports_str,
            component_name=component_name,
            props_interface=props_interface,
            props_destructure=props_destructure,
            jsx_code=jsx_code
        )

        # Write file
        file_path = self.output_dir / "src" / "components" / f"{component_name}.tsx"
        file_path.write_text(self._format_code(code))

        return file_path

    def _generate_props_interface(self, props: Dict[str, Any]) -> str:
        """Generate TypeScript props interface"""
        if not props:
            return ""

        interface_lines = []
        for prop_name, prop_value in props.items():
            prop_type = self._infer_prop_type(prop_name, prop_value)
            interface_lines.append(f"  {prop_name}?: {prop_type};")

        return '\n'.join(interface_lines)

    def _infer_prop_type(self, prop_name: str, prop_value: Any) -> str:
        """Infer TypeScript type from prop name and value"""
        type_mapping = {
            'children': 'React.ReactNode',
            'onClick': '() => void',
            'onChange': '(value: any) => void',
            'onClose': '() => void',
            'isOpen': 'boolean',
            'disabled': 'boolean',
            'variant': 'string',
            'size': 'string',
            'data': 'any[]',
            'value': 'any',
            'placeholder': 'string',
            'title': 'string',
        }

        if prop_name in type_mapping:
            return type_mapping[prop_name]

        if isinstance(prop_value, bool):
            return 'boolean'
        elif isinstance(prop_value, (int, float)):
            return 'number'
        elif isinstance(prop_value, str):
            return 'string'
        elif isinstance(prop_value, list):
            return 'any[]'
        elif isinstance(prop_value, dict):
            return 'object'

        return 'any'

    def _generate_component_jsx(self, component: Dict[str, Any]) -> str:
        """Generate JSX for component"""
        jutro_component = component['jutro_component']
        props = component.get('props', {})
        attributes = component.get('attributes', {})

        # Build props string
        props_str = ' '.join([f'{k}={{{k}}}' for k in props.keys()]) if props else ''

        # Add custom attributes
        if attributes.get('text'):
            props_str += f' >{attributes["text"]}</>'

        jsx = f"<{jutro_component} {props_str} />"
        return jsx

    def _generate_imports(self, components: List[Dict[str, Any]]) -> str:
        """Generate import statements for components"""
        import_lines = set()

        for component in components:
            import_stmt = component.get('import', '')
            if import_stmt:
                import_lines.add(import_stmt)

        return '\n'.join(import_lines)

    def _generate_layout_jsx(self, components: List[Dict[str, Any]]) -> str:
        """Generate layout JSX structure"""
        jsx_lines = []

        for idx, component in enumerate(components):
            component_name = self._sanitize_name(component['figma_name'])
            jsx_lines.append(f"      <{component_name} />")

        return '\n'.join(jsx_lines)

    def _generate_state_hooks(self, components: List[Dict[str, Any]]) -> str:
        """Generate useState hooks for interactive components"""
        hooks = []

        for component in components:
            if component['jutro_component'] in ['Modal', 'Dropdown', 'Tabs']:
                component_name = self._sanitize_name(component['figma_name'])
                hook_name = f"is{component_name}Open"
                hooks.append(f"  const [{hook_name}, set{component_name}Open] = useState(false);")

        return '\n'.join(hooks)

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize component name to valid TypeScript identifier"""
        # Remove special characters and spaces
        name = ''.join(c if c.isalnum() else '_' for c in name)
        # Remove leading numbers
        name = ''.join(c for i, c in enumerate(name) if i == 0 and c.isalpha() or i > 0)
        # Convert to PascalCase
        parts = name.split('_')
        return ''.join(p.capitalize() for p in parts if p)

    @staticmethod
    def _format_code(code: str) -> str:
        """Format code using black/autopep8"""
        try:
            import black
            return black.format_str(code, mode=black.FileMode())
        except Exception:
            return code

    def generate_index_file(self, components: List[str]):
        """Generate index.ts with all component exports"""
        index_content = '\n'.join([
            f"export * from './{Path(f).stem}';"
            for f in components
        ])

        index_path = self.output_dir / "src" / "components" / "index.ts"
        index_path.write_text(index_content)

        logger.info(f"Generated index file: {index_path}")