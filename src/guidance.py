
GENERIC_TIP = "Keep your next blood sugar check, even if you feel well."


def _num(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def personal_tips(a: dict) -> list[str]:
    tips = []
    bmi = _num(a.get("BMI"))
    if bmi is not None and bmi >= 25:
        tips.append("A modest weight loss of around 5% of body weight can improve blood sugar.")
    if a.get("PhysicallyActive") in ("none", "less than half an hour"):
        tips.append("Build up to about 150 minutes of moderate activity a week, such as brisk walking.")
    if a.get("JunkFood") == "Often":
        tips.append("Swap sugary drinks and fried snacks for water, fruit and whole grains.")
    if a.get("Smoking") == "Yes":
        tips.append("Quitting smoking lowers the risk of diabetes and heart disease. Ask a clinic for support.")
    if a.get("highBP") == "Yes" or a.get("BPLevel") == "high":
        tips.append("Keep your blood pressure under regular check and follow your doctor's advice.")
    if a.get("Family_Diabetes") == "Yes" or a.get("Pdiabetes") == "Yes":
        tips.append("With your history, ask for a blood sugar test at your next clinic visit.")
    if a.get("Stress") in ("Very often", "Always"):
        tips.append("Ongoing stress can affect blood sugar. Short breaks, a walk and talking to someone help.")
    if a.get("UriationFreq") == "Quite often":
        tips.append("Passing urine often with thirst can be a warning sign. See a doctor for a blood sugar test.")
    sleep = _num(a.get("Sleep"))
    if sleep is not None and sleep < 6:
        tips.append("Aim for 7 to 9 hours of good sleep, which supports healthy blood sugar.")
    return tips[:5] + [GENERIC_TIP]
