"""Specification for OCR workflow output handling."""

import os
import unittest.mock

from types import SimpleNamespace

from lib import odem
import lib.odem.commons as oc
import lib.odem.ocr.ocr_workflow as odem_wf


def _build_workflow(tmp_path, export_dir=None):
    cfg = odem.get_configparser()
    cfg.add_section(oc.CFG_SEC_OCR)
    cfg.set(oc.CFG_SEC_OCR, 'strip_tags', '')

    odem_process = SimpleNamespace(
        local_mode=True,
        export_dir=export_dir,
        work_dir_root=tmp_path,
        ocr_candidates=[('img_0001.png', 'img_0001')],
        configuration=cfg,
        logger=unittest.mock.Mock(),
        process_identifier='workflow_local',
    )
    return odem_wf.OCRDPageParallel(odem_process)


def test_process_outputs_local_defaults_to_image_dirs(tmp_path):
    """Without export_dir, final OCR stays in the same directories as intermediate OCR files."""

    workflow = _build_workflow(tmp_path, export_dir=None)
    outcome_1 = oc.OCRResult(tmp_path / 'images' / 'set_a' / 'img_0001.xml')
    outcome_2 = oc.OCRResult(tmp_path / 'images' / 'set_b' / 'img_0002.xml')
    outcomes = [outcome_1, outcome_2]

    with unittest.mock.patch('lib.odem.ocr.ocr_workflow.odem_fmt.convert_to_output_format') as mock_convert:
        with unittest.mock.patch('lib.odem.ocr.ocr_workflow.odem_fmt.postprocess_ocr_file') as mock_post:
            mock_convert.side_effect = lambda results, _: results
            workflow.process_outputs(outcomes)

    assert mock_convert.call_count == 2
    expected_dirs = {
        os.path.dirname(outcome_1.local_path),
        os.path.dirname(outcome_2.local_path),
    }
    actual_dirs = {call.args[1] for call in mock_convert.call_args_list}
    assert actual_dirs == expected_dirs
    assert workflow.ocr_results == outcomes
    assert mock_post.call_count == 2


def test_process_outputs_local_uses_export_dir(tmp_path):
    """With export_dir, final OCR is written to that directory."""

    path_export = tmp_path / 'custom_output'
    workflow = _build_workflow(tmp_path, export_dir=path_export)
    outcomes = [oc.OCRResult(tmp_path / 'images' / 'img_0001.xml')]

    with unittest.mock.patch('lib.odem.ocr.ocr_workflow.odem_fmt.convert_to_output_format') as mock_convert:
        with unittest.mock.patch('lib.odem.ocr.ocr_workflow.odem_fmt.postprocess_ocr_file') as mock_post:
            mock_convert.return_value = outcomes
            workflow.process_outputs(outcomes)

    assert path_export.exists()
    assert mock_convert.call_count == 1
    assert mock_convert.call_args.args[1] == str(path_export)
    assert workflow.ocr_results == outcomes
    assert mock_post.call_count == 1
