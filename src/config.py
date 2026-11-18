from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "remotecare_model.joblib"
METADATA_PATH = ROOT / "models" / "model_metadata.json"

MODEL_NOTICE = (
    "Prototype model trained on SYNTHETIC data. It has not been clinically validated "
    "and must not be used to screen real patients."
)
DISCLAIMER = (
    "This tool is a screening aid. It does not diagnose diabetes. A result cannot confirm "
    "or rule out diabetes; appropriate clinical assessment and diagnostic testing are needed."
)

ENTRY_LIMITS = {
    "Age": (18, 100),
    "BMI": (10, 70),
    "Sleep": (0, 24),
    "SoundSleep": (0, 24),
    "Pregnancies": (0, 20),
}
WHOLE_NUMBER_FIELDS = {"Age", "Pregnancies"}


FIELD_INFO = {
    "Age": ("Age (years)", "Age of the person being screened."),
    "Gender": ("Gender", "As recorded in the dataset."),
    "Family_Diabetes": ("Family history of diabetes", "Diabetes in a close family member."),
    "highBP": ("High blood pressure", "Whether the person has been told they have high blood pressure."),
    "PhysicallyActive": ("Physical activity per day", "Typical daily physical activity."),
    "BMI": ("BMI (kg/m²)", "Body Mass Index: weight in kg divided by height in metres squared."),
    "Smoking": ("Smoking", "Whether the person currently smokes."),
    "Alcohol": ("Alcohol use", "Whether the person drinks alcohol."),
    "Sleep": ("Sleep (hours)", "Hours of sleep, as recorded in the dataset."),
    "SoundSleep": ("Sound sleep (hours)", "Hours of uninterrupted sleep, as recorded in the dataset. Confirm the definition against the dataset documentation."),
    "RegularMedicine": ("Regular medication", "Whether the person takes medication regularly."),
    "JunkFood": ("Junk food intake", "How often the person eats junk food."),
    "Stress": ("Stress level", "How often the person reports feeling stressed."),
    "BPLevel": ("Blood-pressure level", "Recorded blood-pressure category."),
    "Pregnancies": ("Pregnancies", "Number of pregnancies. Enter 0 if not applicable."),
    "Pdiabetes": ("Prediabetes", "Whether a prediabetes diagnosis is recorded."),
    "UriationFreq": ("Urination frequency", "How often the person urinates."),
}
