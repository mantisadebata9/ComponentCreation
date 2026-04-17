"""
End-to-end integration tests
"""
import pytest
import sys
from pathlib import Path
import json
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from agent.figma_reader import FigmaReader, FigmaDesign, FigmaFrame
from agent.component_detector import ComponentDetector, ComponentType
from agent.jutro_mapper import JutroComponentMapper
from agent.code_generator import CodeGenerator


@pytest.fixture
def sample_figma_data():
    """Sample Figma API response"""
    return {
        'name': 'Sample Design',
        'document': {
            'children': [
                {
                    'name': 'Page 1',
                    'type': 'PAGE',
                    'children': [
                        {
                            'id': 'frame-1',
                            'name': 'Login Frame',
                            'type': 'FRAME',
                            'absoluteBoundingBox': {
                                'x': 0, 'y': 0, 'width': 400, 'height': 600
                            },
                            'children': [
                                {
                                    'id': 'btn-1',
                                    'name': 'Submit Button',
                                    'type': 'RECTANGLE',
                                    'absoluteBoundingBox': {
                                        'x': 50, 'y': 500, 'width': 300, 'height': 50
                                    },
                                    'fills': [{'color': {'r': 0.2, 'g': 0.6, 'b': 1}}],
                                    'cornerRadius': 8
                                },
                                {
                                    'id': 'input-1',
                                    'name': 'Email Input',
                                    'type': 'RECTANGLE',
                                    'absoluteBoundingBox': {
                                        'x': 50, 'y': 100, 'width': 300, 'height': 40
                                    },
                                    'fills': [{'color': {'r': 0.95, 'g': 0.95, 'b': 0.95}}],
                                    'cornerRadius': 4
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        'styles': {}
    }


def test_figma_reader_parse_response(sample_figma_data):
    """Test parsing Figma API response"""
    reader = FigmaReader()
    design = reader._parse_figma_response(sample_figma_data)

    assert design.project_name == 'Sample Design'
    assert len(design.frames) > 0
    assert isinstance(design, FigmaDesign)

    # Check frame
    frame = design.frames[0]
    assert frame.name == 'Login Frame'
    assert frame.width == 400
    assert frame.height == 600


def test_component_detection():
    """Test component detection"""
    frame_data = {
        'name': 'Test Frame',
        'type': 'FRAME',
        'children': [
            {
                'id': 'btn-1',
                'name': 'Primary Button',
                'type': 'RECTANGLE',
                'absoluteBoundingBox': {
                    'x': 0, 'y': 0, 'width': 120, 'height': 40
                },
                'fills': [{'color': {'r': 0.2, 'g': 0.6, 'b': 1}}],
                'cornerRadius': 8
            },
            {
                'id': 'input-1',
                'name': 'Email Input',
                'type': 'RECTANGLE',
                'absoluteBoundingBox': {
                    'x': 0, 'y': 60, 'width': 300, 'height': 40
                },
                'fills': [{'color': {'r': 0.95, 'g': 0.95, 'b': 0.95}}],
                'cornerRadius': 4
            }
        ]
    }

    detector = ComponentDetector()
    components = detector.detect_from_frame(frame_data)

    assert len(components) > 0
    # Should detect button
    button_detected = any(c.type == ComponentType.BUTTON for c in components)
    assert button_detected


def test_jutro_mapping():
    """Test component mapping to Jutro"""
    frame_data = {
        'name': 'Test Frame',
        'children': [
            {
                'id': 'btn-1',
                'name': 'Primary Button',
                'type': 'RECTANGLE',
                'absoluteBoundingBox': {'x': 0, 'y': 0, 'width': 120, 'height': 40},
                'fills': [{}],
                'cornerRadius': 8
            }
        ]
    }

    detector = ComponentDetector()
    components = detector.detect_from_frame(frame_data)

    mapper = JutroComponentMapper()
    mapped = mapper.map_frame(components)

    assert 'imports' in mapped
    assert 'components' in mapped
    assert len(mapped['components']) > 0

    # Check mapping
    button_mapped = any(c['jutro_component'] == 'Button' for c in mapped['components'])
    assert button_mapped


def test_code_generation():
    """Test code generation"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        generator = CodeGenerator(output_dir=tmp_dir)

        components = [
            {
                'figma_name': 'Primary Button',
                'figma_type': 'Button',
                'figma_id': 'btn-1',
                'jutro_component': 'Button',
                'package': '@jutro/components',
                'import': 'import { Button } from "@jutro/components";',
                'props': {'variant': 'primary', 'children': 'Click me'},
                'children': [],
                'attributes': {'variant': 'primary'},
                'confidence': 0.95
            }
        ]

        files = generator.generate_components(components)
        assert len(files) > 0

        # Check file was created
        generated_file = Path(files[0])
        assert generated_file.exists()
        assert generated_file.suffix == '.tsx'


def test_end_to_end_workflow(sample_figma_data):
    """Test complete workflow"""
    # 1. Parse Figma data
    reader = FigmaReader()
    design = reader._parse_figma_response(sample_figma_data)
    assert design

    # 2. Detect components
    detector = ComponentDetector()
    if design.frames:
        components = detector.detect_from_frame(design.frames[0].properties)
        assert len(components) > 0

        # 3. Map to Jutro
        mapper = JutroComponentMapper()
        mapped = mapper.map_frame(components)
        assert mapped['total'] > 0

        # 4. Generate code
        with tempfile.TemporaryDirectory() as tmp_dir:
            generator = CodeGenerator(output_dir=tmp_dir)
            page_file = generator.generate_page(design.frames[0].name, mapped['components'])
            assert Path(page_file).exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])