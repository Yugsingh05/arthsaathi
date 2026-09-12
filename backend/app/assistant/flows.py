from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Step:
    id: str
    ask: dict[str, str]
    slot: str | None = None
    validate: str | None = None
    error: dict[str, str] = field(default_factory=dict)
    kind: str = "text"
    choices: list[dict] | None = None
    mandatory_note: dict[str, str] = field(default_factory=dict)


LOAN_FLOW: list[Step] = [
    Step("purpose", slot="purpose", kind="choice",
         ask={"en": "What do you need the loan for?",
              "hi": "आपको लोन किस काम के लिए चाहिए?",
              "gu": "તમને લોન કયા કામ માટે જોઈએ છે?"},
         choices=[{"id": "vehicle", "en": "Two-wheeler", "hi": "टू-व्हीलर", "gu": "ટુ-વ્હીલર"},
                  {"id": "business", "en": "Business", "hi": "व्यापार", "gu": "વ્યાપાર"},
                  {"id": "medical", "en": "Medical", "hi": "इलाज", "gu": "સારવાર"},
                  {"id": "education", "en": "Education", "hi": "पढ़ाई", "gu": "ભણતર"}]),
    Step("amount", slot="amount", validate=r"^\D*(\d[\d,]{2,8})\D*$",
         ask={"en": "How much do you need? You can say a number like 50000.",
              "hi": "कितने रुपये चाहिए? जैसे 50000 बोल सकते हैं।",
              "gu": "કેટલા રૂપિયા જોઈએ? જેમ કે 50000 કહી શકો છો."},
         error={"en": "Please tell me an amount in rupees, like 50000.",
                "hi": "कृपया रुपयों में रक़म बताइए, जैसे 50000।",
                "gu": "કૃપા કરી રકમ રૂપિયામાં જણાવો, જેમ કે 50000."}),
    Step("tenure", slot="tenure", kind="choice",
         ask={"en": "Over how many months would you like to repay?",
              "hi": "कितने महीनों में चुकाना चाहेंगे?",
              "gu": "કેટલા મહિનામાં ચૂકવવા માંગો છો?"},
         choices=[{"id": "12", "en": "12 months", "hi": "12 महीने", "gu": "12 મહિના"},
                  {"id": "24", "en": "24 months", "hi": "24 महीने", "gu": "24 મહિના"},
                  {"id": "36", "en": "36 months", "hi": "36 महीने", "gu": "36 મહિના"}]),
    Step("affordability", kind="computed",
         ask={"en": "Let me check this against your income.",
              "hi": "मैं इसे आपकी आमदनी से जाँच लेता हूँ।",
              "gu": "હું આને તમારી આવક સામે તપાસી લઉં છું."}),
    Step("pan", slot="pan", validate=r"^[A-Za-z]{5}\d{4}[A-Za-z]$",
         ask={"en": "Please enter your PAN. This is required by law and cannot be skipped.",
              "hi": "कृपया अपना PAN बताइए। यह क़ानूनन ज़रूरी है और छोड़ा नहीं जा सकता।",
              "gu": "કૃપા કરી તમારો PAN જણાવો. આ કાયદેસર જરૂરી છે અને છોડી શકાય નહીં."},
         error={"en": "A PAN looks like ABCDE1234F. Please check and enter it again.",
                "hi": "PAN ऐसा दिखता है: ABCDE1234F। कृपया दोबारा डालिए।",
                "gu": "PAN આવો દેખાય છે: ABCDE1234F. કૃપા કરી ફરી દાખલ કરો."},
         mandatory_note={"en": "Mandatory KYC step", "hi": "अनिवार्य KYC चरण", "gu": "ફરજિયાત KYC પગલું"}),
    Step("aadhaar_consent", slot="aadhaar_consent", kind="consent",
         ask={"en": "Do you agree to verify your identity with Aadhaar OTP? You can say no and use another document instead.",
              "hi": "क्या आप आधार OTP से पहचान की पुष्टि करने को सहमत हैं? आप मना करके दूसरा दस्तावेज़ भी दे सकते हैं।",
              "gu": "શું તમે આધાર OTP થી ઓળખ ચકાસવા સંમત છો? તમે ના પાડીને બીજો દસ્તાવેજ પણ આપી શકો છો."},
         mandatory_note={"en": "Consent must be explicit, and may be refused",
                         "hi": "सहमति स्पष्ट होनी चाहिए, और मना किया जा सकता है",
                         "gu": "સંમતિ સ્પષ્ટ હોવી જોઈએ, અને ના પાડી શકાય"}),
    Step("kfs", kind="computed",
         ask={"en": "Here is your Key Fact Statement in plain language. Please read it before you accept.",
              "hi": "यह आपका Key Fact Statement सरल भाषा में है। स्वीकार करने से पहले पढ़ लीजिए।",
              "gu": "આ તમારું Key Fact Statement સરળ ભાષામાં છે. સ્વીકારતા પહેલાં વાંચી લો."}),
    Step("done", kind="computed",
         ask={"en": "Your application is with a bank officer. You will get a call in your language within one working day.",
              "hi": "आपका आवेदन बैंक अधिकारी के पास है। एक कार्यदिवस में आपकी भाषा में कॉल आएगी।",
              "gu": "તમારી અરજી બેંક અધિકારી પાસે છે. એક કામકાજના દિવસમાં તમારી ભાષામાં ફોન આવશે."}),
]

ONBOARD_FLOW: list[Step] = [
    Step("language", slot="language", kind="choice",
         ask={"en": "Which language would you like to bank in?",
              "hi": "आप किस भाषा में बैंकिंग करना चाहेंगे?",
              "gu": "તમે કઈ ભાષામાં બેંકિંગ કરવા માંગો છો?"},
         choices=[{"id": "hi", "en": "Hindi", "hi": "हिंदी", "gu": "હિન્દી"},
                  {"id": "gu", "en": "Gujarati", "hi": "गुजराती", "gu": "ગુજરાતી"},
                  {"id": "en", "en": "English", "hi": "अंग्रेज़ी", "gu": "અંગ્રેજી"}]),
    Step("mobile", slot="mobile", validate=r"^[6-9]\d{9}$",
         ask={"en": "What is your mobile number?", "hi": "आपका मोबाइल नंबर क्या है?",
              "gu": "તમારો મોબાઇલ નંબર શું છે?"},
         error={"en": "Please enter a 10-digit mobile number.",
                "hi": "कृपया 10 अंकों का मोबाइल नंबर डालिए।",
                "gu": "કૃપા કરી 10 અંકનો મોબાઇલ નંબર દાખલ કરો."}),
    Step("otp", slot="otp", validate=r"^\d{6}$",
         ask={"en": "Enter the 6-digit OTP we sent you. (Demo: any 6 digits)",
              "hi": "हमने जो 6 अंकों का OTP भेजा है वह डालिए। (डेमो: कोई भी 6 अंक)",
              "gu": "અમે મોકલેલો 6 અંકનો OTP દાખલ કરો. (ડેમો: કોઈ પણ 6 અંક)"},
         error={"en": "The OTP is 6 digits.", "hi": "OTP 6 अंकों का होता है।",
                "gu": "OTP 6 અંકનો હોય છે."}),
    Step("pan", slot="pan", validate=r"^[A-Za-z]{5}\d{4}[A-Za-z]$",
         ask={"en": "Please enter your PAN.", "hi": "कृपया अपना PAN डालिए।",
              "gu": "કૃપા કરી તમારો PAN દાખલ કરો."},
         error={"en": "A PAN looks like ABCDE1234F.", "hi": "PAN ऐसा दिखता है: ABCDE1234F।",
                "gu": "PAN આવો દેખાય છે: ABCDE1234F."},
         mandatory_note={"en": "Mandatory KYC step", "hi": "अनिवार्य KYC चरण", "gu": "ફરજિયાત KYC પગલું"}),
    Step("purpose_consent", slot="purpose_consent", kind="consent",
         ask={"en": "May we read your transactions to personalise what we suggest? You can withdraw this at any time, and banking works without it.",
              "hi": "क्या हम आपके लेन-देन पढ़कर सुझाव निजी बना सकते हैं? आप इसे कभी भी वापस ले सकते हैं, और इसके बिना भी बैंकिंग चलेगी।",
              "gu": "શું અમે તમારા વ્યવહાર વાંચીને સૂચનો વ્યક્તિગત બનાવી શકીએ? તમે આ ગમે ત્યારે પાછું ખેંચી શકો છો, અને એના વગર પણ બેંકિંગ ચાલશે."},
         mandatory_note={"en": "DPDP: purpose-specific and withdrawable",
                         "hi": "DPDP: उद्देश्य-विशिष्ट और वापस लेने योग्य",
                         "gu": "DPDP: હેતુ-વિશિષ્ટ અને પાછું ખેંચી શકાય"}),
    Step("done", kind="computed",
         ask={"en": "You are all set. Your account is ready to use.",
              "hi": "सब तैयार है। आपका खाता इस्तेमाल के लिए तैयार है।",
              "gu": "બધું તૈયાર છે. તમારું ખાતું વાપરવા માટે તૈયાર છે."}),
]

FLOWS = {"loan": LOAN_FLOW, "onboarding": ONBOARD_FLOW}

YES = re.compile(r"^(y|yes|ha|haan|હા|हाँ|हां|ok|okay|sure|theek|ઓકે)", re.I)
NO = re.compile(r"^(n|no|nahi|ના|नहीं|na)", re.I)
