from app import build_grounded_srd_block


def test_build_grounded_srd_block_contains_required_markers():
    payload = {
        "name": "Fighter",
        "hit_die": 10,
        "primary_abilities": ["Strength", "Dexterity"],
        "saving_throw_proficiencies": ["Strength", "Constitution"],
        "proficiencies": ["All armor", "Shields", "Simple weapons", "Martial weapons"],
        "features_by_level": [
            {"level": 1, "features": [{"name": "Fighting Style"}, {"name": "Second Wind"}]},
            {"level": 2, "features": [{"name": "Action Surge"}]},
        ],
    }

    txt = build_grounded_srd_block(payload, target_level=2)

    # Basic structure markers
    assert "Grounded SRD Facts" in txt
    assert "- Class: Fighter" in txt
    assert "- Hit Die: d10" in txt

    # Feature names included up to target level
    assert "Level 1: Fighting Style" in txt
    assert "Level 1: Second Wind" in txt
    assert "Level 2: Action Surge" in txt

    # Safety rule marker
    assert "authoritative SRD truth" in txt
    assert "SRD limitation" in txt


def test_build_grounded_srd_block_handles_missing_features():
    payload = {"name": "Wizard", "hit_die": 6, "features_by_level": []}
    txt = build_grounded_srd_block(payload, target_level=1)
    assert "- Class: Wizard" in txt
    assert "Features: (not available from grounding payload)" in txt
