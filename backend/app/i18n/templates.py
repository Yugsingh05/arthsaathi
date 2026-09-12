from __future__ import annotations

LANGS = ("en", "hi", "gu")

LANG_NAMES = {"en": "English", "hi": "हिंदी", "gu": "ગુજરાતી"}


def inr(x: float) -> str:
    n = int(round(x))
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if n < 0 else "") + "₹" + s


REASON_TEMPLATES: dict[str, dict[str, str]] = {
    "savings_rate+": {
        "en": "You have saved about {save_amt} every month for the last six months.",
        "hi": "आपने पिछले 6 महीने हर महीने {save_amt} बचाए हैं।",
        "gu": "તમે છેલ્લા 6 મહિનાથી દર મહિને {save_amt} બચાવો છો.",
    },
    "salary_regularity+": {
        "en": "Your income arrives on the same days every month.",
        "hi": "आपकी आमदनी हर महीने तय दिनों पर आती है।",
        "gu": "તમારી આવક દર મહિને નિયત દિવસે આવે છે.",
    },
    "emi_to_income-": {
        "en": "Your EMIs take only {emi_pct}% of your monthly income.",
        "hi": "आपकी EMI आपकी मासिक आय का सिर्फ़ {emi_pct}% है।",
        "gu": "તમારી EMI તમારી માસિક આવકના ફક્ત {emi_pct}% છે.",
    },
    "emi_to_income+": {
        "en": "Your EMIs already take {emi_pct}% of your monthly income.",
        "hi": "आपकी EMI पहले से आपकी आय का {emi_pct}% ले रही है।",
        "gu": "તમારી EMI પહેલેથી તમારી આવકના {emi_pct}% લે છે.",
    },
    "avg_balance_30d+": {
        "en": "Your account has held an average balance of {avg_bal} this month.",
        "hi": "इस महीने आपके खाते में औसतन {avg_bal} रहे हैं।",
        "gu": "આ મહિને તમારા ખાતામાં સરેરાશ {avg_bal} રહ્યા છે.",
    },
    "cash_share+": {
        "en": "A large part of your spending is in cash.",
        "hi": "आपका ज़्यादातर ख़र्च नक़द में होता है।",
        "gu": "તમારો મોટાભાગનો ખર્ચ રોકડમાં થાય છે.",
    },
    "monthly_income+": {
        "en": "Based on your monthly income of about {income}.",
        "hi": "आपकी लगभग {income} मासिक आय के आधार पर।",
        "gu": "તમારી અંદાજે {income} માસિક આવકના આધારે.",
    },
    "income_volatility+": {
        "en": "Your income changes a lot from month to month.",
        "hi": "आपकी आमदनी हर महीने बदलती रहती है।",
        "gu": "તમારી આવક દર મહિને બદલાતી રહે છે.",
    },
    "digital_share+": {
        "en": "Most of your payments are already digital.",
        "hi": "आपके ज़्यादातर भुगतान पहले से डिजिटल हैं।",
        "gu": "તમારી મોટાભાગની ચુકવણી પહેલેથી ડિજિટલ છે.",
    },
    "months_on_book+": {
        "en": "You have banked with us for {years} years.",
        "hi": "आप {years} साल से हमारे साथ हैं।",
        "gu": "તમે {years} વર્ષથી અમારી સાથે છો.",
    },
    "discretionary_share+": {
        "en": "Your everyday spending leaves room to set money aside.",
        "hi": "आपके रोज़ के ख़र्च के बाद बचत की गुंजाइश है।",
        "gu": "તમારા રોજિંદા ખર્ચ પછી બચતની જગ્યા છે.",
    },
}

PRODUCT_BENEFIT: dict[str, dict[str, str]] = {
    "rd_2000": {
        "en": "A recurring deposit could earn you 6.5% interest.",
        "hi": "रिकरिंग डिपॉज़िट पर 6.5% ब्याज मिलेगा।",
        "gu": "રિકરિંગ ડિપોઝિટથી 6.5% વ્યાજ મળી શકે.",
    },
    "sip_1000": {
        "en": "A ₹1,000 monthly SIP can be started and stopped any time.",
        "hi": "₹1,000 की मासिक SIP कभी भी शुरू या बंद की जा सकती है।",
        "gu": "₹1,000ની માસિક SIP ગમે ત્યારે શરૂ કે બંધ કરી શકાય.",
    },
    "sweep_fd": {
        "en": "Balance above ₹25,000 can earn FD rates automatically.",
        "hi": "₹25,000 से ऊपर की राशि पर अपने आप FD ब्याज मिलेगा।",
        "gu": "₹25,000થી વધુ રકમ પર આપમેળે FD વ્યાજ મળશે.",
    },
    "health_cover": {
        "en": "Health cover of ₹5 lakh costs about ₹520 a month.",
        "hi": "₹5 लाख का हेल्थ कवर लगभग ₹520 महीना।",
        "gu": "₹5 લાખનું હેલ્થ કવર અંદાજે ₹520 પ્રતિ માસ.",
    },
    "accident_cover": {
        "en": "Accident cover of ₹2 lakh costs ₹20 a month.",
        "hi": "₹2 लाख का दुर्घटना कवर ₹20 महीना।",
        "gu": "₹2 લાખનું અકસ્માત કવર ₹20 પ્રતિ માસ.",
    },
    "kcc": {
        "en": "A Kisan Credit Card gives crop credit at 4% with the interest subvention.",
        "hi": "किसान क्रेडिट कार्ड पर ब्याज छूट के साथ 4% दर।",
        "gu": "કિસાન ક્રેડિટ કાર્ડ પર વ્યાજ છૂટ સાથે 4% દર.",
    },
    "gold_loan": {
        "en": "A gold loan costs far less than an unsecured loan, at about 9%.",
        "hi": "गोल्ड लोन असुरक्षित लोन से सस्ता है, लगभग 9%।",
        "gu": "ગોલ્ડ લોન અસુરક્ષિત લોન કરતાં સસ્તી છે, આશરે 9%.",
    },
    "two_wheeler_loan": {
        "en": "A two-wheeler loan starts at 10.5% for 36 months.",
        "hi": "टू-व्हीलर लोन 36 महीने के लिए 10.5% से शुरू।",
        "gu": "ટુ-વ્હીલર લોન 36 મહિના માટે 10.5%થી શરૂ.",
    },
    "personal_loan": {
        "en": "A personal loan is available at 13.5%. Interest applies from day one.",
        "hi": "पर्सनल लोन 13.5% पर उपलब्ध है। ब्याज पहले दिन से लगेगा।",
        "gu": "પર્સનલ લોન 13.5% પર ઉપલબ્ધ છે. વ્યાજ પહેલા દિવસથી લાગશે.",
    },
    "top_up_loan": {
        "en": "A top-up on your existing loan is available at 12.9%.",
        "hi": "आपके मौजूदा लोन पर टॉप-अप 12.9% पर उपलब्ध है।",
        "gu": "તમારી હાલની લોન પર ટોપ-અપ 12.9% પર ઉપલબ્ધ છે.",
    },
    "credit_card": {
        "en": "A credit card with no joining fee. Interest is 3.5% a month if unpaid.",
        "hi": "बिना जॉइनिंग फ़ीस का क्रेडिट कार्ड। बकाया पर 3.5% मासिक ब्याज।",
        "gu": "જોઇનિંગ ફી વગરનું ક્રેડિટ કાર્ડ. બાકી રકમ પર 3.5% માસિક વ્યાજ.",
    },
}

PRODUCT_NAME: dict[str, dict[str, str]] = {
    "rd_2000": {"en": "Recurring Deposit", "hi": "रिकरिंग डिपॉज़िट", "gu": "રિકરિંગ ડિપોઝિટ"},
    "sip_1000": {"en": "Monthly SIP", "hi": "मासिक SIP", "gu": "માસિક SIP"},
    "sweep_fd": {"en": "Savings Sweep FD", "hi": "स्वीप एफ़डी", "gu": "સ્વીપ એફડી"},
    "health_cover": {"en": "Health Cover", "hi": "हेल्थ कवर", "gu": "હેલ્થ કવર"},
    "accident_cover": {"en": "Accident Cover", "hi": "दुर्घटना कवर", "gu": "અકસ્માત કવર"},
    "kcc": {"en": "Kisan Credit Card", "hi": "किसान क्रेडिट कार्ड", "gu": "કિસાન ક્રેડિટ કાર્ડ"},
    "gold_loan": {"en": "Gold Loan", "hi": "गोल्ड लोन", "gu": "ગોલ્ડ લોન"},
    "two_wheeler_loan": {"en": "Two-Wheeler Loan", "hi": "टू-व्हीलर लोन", "gu": "ટુ-વ્હીલર લોન"},
    "personal_loan": {"en": "Personal Loan", "hi": "पर्सनल लोन", "gu": "પર્સનલ લોન"},
    "top_up_loan": {"en": "Top-up Loan", "hi": "टॉप-अप लोन", "gu": "ટોપ-અપ લોન"},
    "credit_card": {"en": "Credit Card", "hi": "क्रेडिट कार्ड", "gu": "ક્રેડિટ કાર્ડ"},
}

UI: dict[str, dict[str, str]] = {
    "why_this": {"en": "Why am I seeing this?", "hi": "यह मुझे क्यों दिख रहा है?", "gu": "આ મને કેમ દેખાય છે?"},
    "ai_label": {"en": "AI suggestion", "hi": "AI सुझाव", "gu": "AI સૂચન"},
    "talk_banker": {"en": "Talk to a banker", "hi": "बैंकर से बात करें", "gu": "બેંકર સાથે વાત કરો"},
    "held_back": {"en": "Offers we held back", "hi": "रोके गए ऑफ़र", "gu": "રોકેલા ઓફર"},
    "tell_me_more": {"en": "Tell me more", "hi": "और बताइए", "gu": "વધુ જણાવો"},
    "requested": {"en": "A banker will call you", "hi": "बैंकर आपको कॉल करेंगे",
                  "gu": "બેંકર તમને ફોન કરશે"},
    "recent": {"en": "Recent activity", "hi": "हाल के लेन-देन", "gu": "તાજેતરના વ્યવહાર"},
    "hardship_title": {"en": "We noticed a difficult month", "hi": "हमें एक मुश्किल महीना दिखा",
                       "gu": "અમને એક મુશ્કેલ મહિનો દેખાયો"},
    "hardship_body": {
        "en": "Your income is down and an EMI did not go through. You can take a one-month EMI holiday, or your branch can call you.",
        "hi": "आपकी आमदनी घटी है और एक EMI नहीं कट पाई। आप एक महीने की EMI छुट्टी ले सकते हैं, या शाखा आपको कॉल करेगी।",
        "gu": "તમારી આવક ઘટી છે અને એક EMI કપાઈ નથી. તમે એક મહિનાની EMI રજા લઈ શકો છો, અથવા શાખા તમને ફોન કરશે.",
    },
    "fraud_title": {"en": "We have paused four transfers", "hi": "हमने चार ट्रांसफ़र रोके हैं",
                    "gu": "અમે ચાર ટ્રાન્સફર રોક્યા છે"},
    "fraud_body": {
        "en": "Four transfers to new payees at 2am did not match how you usually pay. Your money is still in your account. We will call to confirm.",
        "hi": "रात 2 बजे नए पेयी को चार ट्रांसफ़र आपके सामान्य तरीक़े से मेल नहीं खाते। आपका पैसा आपके खाते में सुरक्षित है। हम पुष्टि के लिए कॉल करेंगे।",
        "gu": "રાત્રે 2 વાગ્યે નવા પેયીને ચાર ટ્રાન્સફર તમારી સામાન્ય રીત સાથે મેળ ખાતા નથી. તમારા પૈસા તમારા ખાતામાં સુરક્ષિત છે. અમે પુષ્ટિ માટે ફોન કરીશું.",
    },
}


def t(bucket: dict, key: str, lang: str) -> str:
    entry = bucket.get(key) or {}
    return entry.get(lang) or entry.get("en") or ""
