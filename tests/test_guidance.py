from __future__ import annotations

from lander_sim.control.guidance import make_hop_landing_profile, make_hover_profile, make_lateral_translation_profile



def test_hover_profile_returns_single_target() -> None:
    profile = make_hover_profile(altitude_m=15.0, duration_s=5.0)
    target = profile.sample(3.0)
    assert target.z == 15.0
    assert target.label == 'hover'



def test_lateral_translation_profile_reaches_target_segment() -> None:
    profile = make_lateral_translation_profile(target_x_m=8.0)
    assert profile.sample(0.5).x == 0.0
    assert profile.sample(3.0).x == 8.0
    assert profile.sample(8.5).x == 8.0



def test_hop_profile_descends_to_ground_target() -> None:
    profile = make_hop_landing_profile(ascent_altitude_m=18.0)
    assert profile.sample(0.5).z == 18.0
    assert profile.sample(4.0).z == 0.0
