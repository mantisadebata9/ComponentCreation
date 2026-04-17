"""
Jutro Component Mapper - Maps detected components to Guidewire Jutro components
"""
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from .component_detector import ComponentType, DetectedComponent

logger = logging.getLogger(__name__)


class JutroComponentMapper:
    """
    Maps Figma components to Guidewire Jutro Storybook components
    Maintains a configurable mapping system
    """

    # Default Figma → Jutro mappings
    DEFAULT_MAPPING = {
        ComponentType.BUTTON: {
            'jutro_component': 'Button',
            'package': '@jutro/components',
            'import': 'import { Button } from "@jutro/components";',
            'props': ['variant', 'size', 'disabled', 'onClick', 'children'],
            'defaults': {'variant': 'primary', 'size': 'md'}
        },
        ComponentType.INPUT: {
            'jutro_component': 'TextInput',
            'package': '@jutro/components',
            'import': 'import { TextInput } from "@jutro/components";',
            'props': ['label', 'placeholder', 'value', 'onChange', 'error'],
            'defaults': {'size': 'md'}
        },
        ComponentType.CARD: {
            'jutro_component': 'Panel',
            'package': '@jutro/components',
            'import': 'import { Panel } from "@jutro/components";',
            'props': ['title', 'children', 'footer'],
            'defaults': {}
        },
        ComponentType.HEADER: {
            'jutro_component': 'PageHeader',
            'package': '@jutro/components',
            'import': 'import { PageHeader } from "@jutro/components";',
            'props': ['title', 'subtitle', 'actions'],
            'defaults': {}
        },
        ComponentType.NAVIGATION: {
            'jutro_component': 'Navigation',
            'package': '@jutro/components',
            'import': 'import { Navigation } from "@jutro/components";',
            'props': ['items', 'activeItem', 'onChange'],
            'defaults': {}
        },
        ComponentType.GRID: {
            'jutro_component': 'GridLayout',
            'package': '@jutro/components',
            'import': 'import { GridLayout } from "@jutro/components";',
            'props': ['columns', 'gap', 'children'],
            'defaults': {'columns': 12, 'gap': '16px'}
        },
        ComponentType.BADGE: {
            'jutro_component': 'Badge',
            'package': '@jutro/components',
            'import': 'import { Badge } from "@jutro/components";',
            'props': ['variant', 'children'],
            'defaults': {'variant': 'default'}
        },
        ComponentType.MODAL: {
            'jutro_component': 'Modal',
            'package': '@jutro/components',
            'import': 'import { Modal } from "@jutro/components";',
            'props': ['title', 'isOpen', 'onClose', 'children'],
            'defaults': {}
        },
        ComponentType.TABLE: {
            'jutro_component': 'Table',
            'package': '@jutro/components',
            'import': 'import { Table } from "@jutro/components";',
            'props': ['columns', 'data', 'onRowClick'],
            'defaults': {}
        },
        ComponentType.DROPDOWN: {
            'jutro_component': 'Select',
            'package': '@jutro/components',
            'import': 'import { Select } from "@jutro/components";',
            'props': ['options', 'value', 'onChange', 'placeholder'],
            'defaults': {}
        },
        ComponentType.TABS: {
            'jutro_component': 'Tabs',
            'package': '@jutro/components',
            'import': 'import { Tabs } from "@jutro/components";',
            'props': ['tabs', 'activeTab', 'onChange'],
            'defaults': {}
        },
        ComponentType.ALERT: {
            'jutro_component': 'Alert',
            'package': '@jutro/components',
            'import': 'import { Alert } from "@jutro/components";',
            'props': ['type', 'title', 'message'],
            'defaults': {'type': 'info'}
        },
        ComponentType.TEXT: {
            'jutro_component': 'Typography',
            'package': '@jutro/components',
            'import': 'import { Typography } from "@jutro/components";',
            'props': ['variant', 'children'],
            'defaults': {'variant': 'body'}
        },
        ComponentType.CONTAINER: {
            'jutro_component': 'Box',
            'package': '@jutro/components',
            'import': 'import { Box } from "@jutro/components";',
            'props': ['padding', 'margin', 'children'],
            'defaults': {}
        },
    }

    def __init__(self, custom_mapping_path: Optional[str] = None):
        self.mapping = self.DEFAULT_MAPPING.copy()

        if custom_mapping_path and Path(custom_mapping_path).exists():
            self._load_custom_mapping(custom_mapping_path)

    def map_component(self, detected_component: DetectedComponent) -> Dict[str, Any]:
        """
        Map a detected component to Jutro component
        Returns mapping with import statement and props
        """
        component_type = detected_component.type
        mapping = self.mapping.get(component_type)

        if not mapping:
            logger.warning(f"No mapping found for {component_type}")
            mapping = self.mapping[ComponentType.CONTAINER]

        mapped = {
            'figma_name': detected_component.name,
            'figma_type': component_type.value,
            'figma_id': detected_component.id,
            'jutro_component': mapping['jutro_component'],
            'package': mapping['package'],
            'import': mapping['import'],
            'props': self._map_props(
                detected_component,
                mapping['props'],
                mapping['defaults']
            ),
            'children': detected_component.children,
            'attributes': detected_component.attributes,
            'confidence': detected_component.confidence
        }

        return mapped

    def map_frame(self, components: List[DetectedComponent]) -> Dict[str, Any]:
        """
        Map all components in a frame to Jutro components
        """
        mapped_components = []
        imports = set()

        for component in components:
            mapped = self.map_component(component)
            mapped_components.append(mapped)
            imports.add(mapped['import'])

        return {
            'imports': list(imports),
            'components': mapped_components,
            'total': len(mapped_components)
        }

    def _map_props(self, component: DetectedComponent, prop_names: List[str], defaults: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map component properties and attributes to Jutro props
        """
        props = defaults.copy()

        # Map from attributes
        attributes = component.attributes
        properties = component.properties

        # Map common props
        prop_mapping = {
            'text': 'children',
            'fontSize': 'size',
            'fontWeight': 'weight',
            'fontFamily': 'font',
            'cornerRadius': 'rounded',
            'width': 'width',
            'height': 'height',
        }

        for attr_key, attr_value in attributes.items():
            prop_key = prop_mapping.get(attr_key, attr_key)
            if prop_key in prop_names and attr_value is not None:
                props[prop_key] = attr_value

        # Add properties
        for prop in prop_names:
            if prop not in props and prop in properties:
                props[prop] = properties[prop]

        return props

    def _load_custom_mapping(self, mapping_path: str):
        """Load custom component mapping from JSON"""
        try:
            with open(mapping_path, 'r') as f:
                custom_mapping = json.load(f)

            for comp_type_str, mapping in custom_mapping.items():
                try:
                    comp_type = ComponentType[comp_type_str]
                    self.mapping[comp_type] = mapping
                except KeyError:
                    logger.warning(f"Unknown component type: {comp_type_str}")

            logger.info(f"Loaded custom mapping from {mapping_path}")

        except Exception as e:
            logger.error(f"Error loading custom mapping: {e}")