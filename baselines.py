from nistsp800_53 import Baseline, Library, Nist_sp_800_53_r4, Nist_sp_800_53_r5

def extract_baselines(library: Library) -> tuple[list[str], list[str], list[str], list[str]]:
    """
    Extracts the low, moderate, high and privacy baselines from the Library objects.
    """
    low = {}
    moderate = {}
    high = {}
    privacy = {}

    baseline_mapping_dict = {
        "LOW": low,
        "MODERATE": moderate,
        "HIGH": high,
        "PRIVACY": privacy
    }
    
    for control_idx in library.controls.keys():
        if library.controls[control_idx].baseline_impact:
            try:
                for baseline_value in library.controls[control_idx].baseline_impact:
                    baseline_mapping_dict[baseline_value][control_idx] = []
            except KeyError:
                pass
        for control_enhancement_idx in library.controls[control_idx].control_enhancements.keys():
            if library.controls[control_idx].control_enhancements[control_enhancement_idx].baseline_impact:
                try:
                    for baseline_value in library.controls[control_idx].control_enhancements[control_enhancement_idx].baseline_impact:
                        baseline_mapping_dict[baseline_value][control_idx].append(control_enhancement_idx)
                except KeyError:
                    pass
    
    return privacy, low, moderate, high


privacy, low, moderate, high = extract_baselines(Nist_sp_800_53_r4())

baseline_nist_sp_800_53_r4_privacy = Baseline(controls=privacy, name='Privacy', revision=4)
baseline_nist_sp_800_53_r4_low = Baseline(controls=low,  name='Low', revision=4)
baseline_nist_sp_800_53_r4_moderate = Baseline(controls=moderate,  name='Moderate', revision=4)
baseline_nist_sp_800_53_r4_high = Baseline(controls=high,  name='High', revision=4)

print(low)

del privacy
del low
del moderate
del high

privacy, low, moderate, high = extract_baselines(Nist_sp_800_53_r5())
print(low)

baseline_nist_sp_800_53_r5_privacy = Baseline(controls=privacy, name='Privacy', revision=5)
baseline_nist_sp_800_53_r5_low = Baseline(controls=low,  name='Low', revision=5)
baseline_nist_sp_800_53_r5_moderate = Baseline(controls=moderate,  name='Moderate', revision=5)
baseline_nist_sp_800_53_r5_high = Baseline(controls=high,  name='High', revision=5)