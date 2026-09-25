import numpy as np

from robotic_surgery.learning_pipeline.config import PipelineConfig, QualityConfig
from robotic_surgery.learning_pipeline.preprocessing.io import read_frames
from robotic_surgery.learning_pipeline.preprocessing.privacy import PrivacyRedactor
from robotic_surgery.learning_pipeline.preprocessing.quality import QualityFilter
from robotic_surgery.learning_pipeline.preprocessing.sampling import sample_frames
from robotic_surgery.learning_pipeline.preprocessing.segmentation import segment_shots
from robotic_surgery.learning_pipeline.data.sources import ResearchDatasetSource
from robotic_surgery.learning_pipeline.types import FrameStack


def _ref():
    return next(ResearchDatasetSource("ego4d", "d").fetch(limit=1))


def test_read_frames_shape():
    ref = _ref()
    frames = read_frames(ref, max_frames=20)
    assert frames.ndim == 4 and frames.shape[-1] == 3
    assert frames.dtype == np.uint8


def test_segmentation_covers_all_frames():
    ref = _ref()
    frames = read_frames(ref)
    shots = segment_shots(frames, ref)
    assert shots[0].start_frame == 0
    assert shots[-1].end_frame == frames.shape[0]
    # contiguous, non-overlapping
    for a, b in zip(shots, shots[1:]):
        assert a.end_frame == b.start_frame


def test_sampling_respects_fps():
    ref = _ref()
    frames = read_frames(ref)
    shots = segment_shots(frames, ref)
    stack = sample_frames(frames, shots[0], ref, target_fps=2.0)
    assert isinstance(stack, FrameStack)
    assert stack.num_frames >= 1
    assert stack.num_frames <= shots[0].num_frames


def test_quality_rejects_low_resolution():
    tiny = FrameStack(frames=np.zeros((3, 10, 10, 3), np.uint8),
                      frame_indices=[0, 1, 2], sample_fps=2.0)
    qf = QualityFilter(QualityConfig(min_resolution=240))
    report = qf.assess(tiny)
    assert not report.passed
    assert "resolution" in report.reason


def test_quality_passes_structured_frames():
    ref = _ref()
    frames = read_frames(ref)
    from robotic_surgery.learning_pipeline.preprocessing.segmentation import segment_shots
    shots = segment_shots(frames, ref)
    stack = sample_frames(frames, shots[0], ref, target_fps=4.0)
    # relax resolution floor since synthetic frames are small
    qf = QualityFilter(QualityConfig(min_resolution=64))
    assert qf.assess(stack).passed


def test_privacy_redaction_changes_pixels():
    ref = _ref()
    frames = read_frames(ref)
    stack = FrameStack(frames=frames[:5], frame_indices=list(range(5)), sample_fps=4.0)
    redactor = PrivacyRedactor()
    out, report = redactor.redact(stack)
    assert out.frames.shape == stack.frames.shape
    # a face-like blob exists in the synthetic frames, so something is redacted
    assert report.faces_redacted >= 1
