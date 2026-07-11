import re


# =========================
# Helpers for constants
# =========================

def _kw(text):
    return [x.strip() for x in text.split("|") if x.strip()]


def dedupe_list(items):
    seen = set()
    result = []
    for item in items:
        key = item.lower() if isinstance(item, str) else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


# =========================
# Student keyword constants
# =========================

STUDENT_KEYWORDS = _kw("""
student|students|class|classes|lecture|lectures|course|courses|timetable|schedule|calendar|semester|
assignment|assignments|homework|quiz|quizzes|project|projects|presentation|deadline|submission|submit|
exam|examination|midterm|final exam|result|results|grade|grades|gpa|marks|attendance|absence|leave|
student id|id card|library|scholarship|tuition|fee|payment|event|workshop|competition|internship|
registration|register|academic|notice|announcement|

meeting|meet|group meeting|team meeting|project meeting|discussion|group discussion|presentation file|slides|
slide|ppt|pptx|demo|viva|report|essay|lab|practical|tutorial|online class|zoom class|google meet|classroom|
teacher|lecturer|professor|department|major|module|subject|campus|school|college|university|admin office|
student affairs|dean|rector|certificate|seminar|training|test|mock test|assessment|rubric|group project|
individual assignment|submit by|due date|extension|late submission|make up class|reschedule|postponed|
cancelled class|class cancelled|exam room|seat plan|hall ticket|admission|enrollment|enroll|orientation|
convocation|graduation|transcript|

student registration|student information system|student enrollment|student portal|student login|student account|
application form|entrance exam|admission requirements|course registration|exam registration|academic calendar|
class timetable|course syllabus|syllabus|curriculum|academic regulation|academic guide|handbook|
learning management system|lms|online course|online courses|student registration system|campus life|
campus facilities|campus tour|hostel|male hostel|female hostel|dormitory|student activities|e-library|
library management system|degree programme|degree program|bachelor degree|master degree|doctoral degree|phd|diploma|
computer science|computer technology|information technology|computing science|software engineering|knowledge engineering|
high performance computing|business information systems|ict engineering|research|applied research|ict research|
research repository|semantic web|image processing|signal processing|natural language processing|digital transformation|
ict innovation|science fair|application contest|quiz competition|student awards|graduation ceremony|

ucsy|ucsm|uit|ucstt|university of computer studies yangon|university of computer studies mandalay|
university of information technology|university of computer studies thaton|ucsy.edu.mm|ucsm.edu.mm|uit.edu.mm|ucstt.edu.mm|
edu.mm|student.edu.mm|

ကျောင်းသား|ကျောင်းသူ|အတန်း|စာသင်ခန်း|သင်ခန်းစာ|ဘာသာရပ်|အချိန်ဇယား|စာသင်ချိန်|နှစ်ဝက်|စမတ်စတာ|
အက်ဆိုင်းမန့်|အိမ်စာ|ပရောဂျက်|ပရဆင်တေးရှင်း|စာမေးပွဲ|မစ်တမ်း|ဖိုင်နယ်|အောင်စာရင်း|ရလဒ်|
အမှတ်|အဆင့်|ဂရိတ်|တက်ရောက်မှု|ခွင့်|ခွင့်တိုင်|နောက်ဆုံးရက်|သတ်မှတ်ရက်|နောက်ဆုံးထား|
မေဂျာ|နုတ်စ်|စာအုပ်|ကျောင်းသားကတ်|စာကြည့်တိုက်|ပညာသင်ဆု|ကျောင်းလခ|ငွေသွင်း|ငွေပေးချေ|
ကြေညာချက်|အသိပေးစာ|စာရင်းသွင်း|တင်သွင်း|

မီတင်|အစည်းအဝေး|တွေ့ဆုံ|ဆွေးနွေး|ယူလာခဲ့|ယူလာ|ပြန်ပေး|ပြန်ကြား|အကြောင်းပြန်|မလာနိုင်|
မတက်နိုင်|လာခဲ့|တက်ရောက်|ပါဝင်|ပြင်ဆင်|ဖိုင်ယူလာ|စလိုက်|ပရဆင်တေးရှင်းဖိုင်|တင်ပြ|
လက်ချာ|လက်တွေ့ခန်း|အွန်လိုင်းအတန်း|ဆရာ|ဆရာမ|ပါမောက္ခ|ဌာန|ဌာနမှူး|တက္ကသိုလ်|ကောလိပ်|
ကျောင်း|ပညာရေး|ဖောင်|ပြေစာ|လျှောက်ထား|ဝပ်ရှော့|သင်တန်း|ပြိုင်ပွဲ|လက်မှတ်|ဆွေးနွေးပွဲ|
ဘွဲ့နှင်းသဘင်|အောင်လက်မှတ်|မှတ်တမ်း|စာရွက်စာတမ်း|

ဝင်ခွင့်|ဝင်ခွင့်လျှောက်လွှာ|ဝင်ခွင့်စာမေးပွဲ|ကျောင်းသားရေးရာ|ကျောင်းသားအချက်အလက်စနစ်|
ကျောင်းသားမှတ်ပုံတင်|ကျောင်းသားစာရင်းသွင်း|ပညာသင်နှစ်|ပညာရေးပြက္ခဒိန်|အတန်းချိန်ဇယား|
စာသင်ချိန်ဇယား|သင်ရိုး|သင်ရိုးညွှန်းတမ်း|သင်တန်းဖွင့်လှစ်ခြင်း|အလုပ်သင်|သုတေသန|
သင်ကြားရေးစနစ်|အွန်လိုင်းသင်ကြားရေး|အဆောင်|ကျောင်းသားဆု|ကျောင်းသားလှုပ်ရှားမှု|သိပ္ပံပြပွဲ|
ကွန်ပျူတာသိပ္ပံ|ကွန်ပျူတာနည်းပညာ|သတင်းအချက်အလက်နည်းပညာ|ပညာရေးရုံး|
ကွန်ပျူတာတက္ကသိုလ်|သတင်းအချက်အလက်နည်းပညာတက္ကသိုလ်
""")


TRUSTED_STUDENT_DOMAINS = dedupe_list(_kw("""
ucstt.edu.mm|ucsy.edu.mm|ucsm.edu.mm|uit.edu.mm|student.edu.mm|st.edu.mm|edu.mm|.edu|.ac|.edu.mm
"""))


STUDENT_IMPORTANCE_HIGH = _kw("""
urgent|deadline|today|tomorrow|exam|payment|registration|scholarship|submit by|final notice|
due today|due tomorrow|last date|final deadline|important notice|must attend|required|compulsory|
immediately|as soon as possible|asap|final exam|midterm|quiz|test|presentation tomorrow|
meeting tomorrow|tomorrow meeting|3 pm meeting|reply|reply back|confirm attendance|cannot attend|
bring|bring file|bring presentation|hall ticket|seat plan|exam room|fee payment|late fee|

entrance exam|application form|student registration|course registration|exam registration|
registration deadline|admission deadline|admission open|registration open|important announcement|
official announcement|class timetable|academic calendar|internship application|graduation ceremony|

ယနေ့|ဒီနေ့|မနက်ဖြန်|အရေးကြီး|အမြန်|နောက်ဆုံးထား|နောက်ဆုံးရက်|သတ်မှတ်ရက်|စာမေးပွဲ|
ငွေပေးချေ|စာရင်းသွင်း|ပညာသင်ဆု|မနက်ဖြန် meeting|မနက်ဖြန် မီတင်|မလာနိုင်ရင်|
ပြန်ပေး|ပြန်ကြား|ယူလာခဲ့|တက်ရောက်ရန်လိုအပ်|မဖြစ်မနေ|အတည်ပြု|အမြန်ဆုံး|
စာမေးပွဲခန်း|ခုံနံပါတ်|ကျောင်းလခ|နောက်ကျကြေး|ဝင်ခွင့်|ဝင်ခွင့်လျှောက်လွှာ|
ဝင်ခွင့်စာမေးပွဲ|ကျောင်းသားမှတ်ပုံတင်|သင်တန်းဖွင့်လှစ်မည်|အရေးကြီးကြေညာချက်|
ဘွဲ့နှင်းသဘင်|အလုပ်သင်
""")


STUDENT_ACTION_KEYWORDS = _kw("""
submit|reply|send|fill|complete|register|pay|attend|bring|check|confirm|apply|upload|
prepare|read|review|download|print|sign|join|come|participate|present|practice|
bring file|bring presentation|reply back|respond|update|verify|collect|receive|contact|
rename|fix|push|merge|export|

register online|course register|apply admission|download form|check result|view timetable|
access lms|login|sign in|submit application|course selection|register course|

တင်သွင်း|ပေးပို့|ဖြည့်စွက်|စာရင်းသွင်း|ငွေပေးချေ|တက်ရောက်|ယူဆောင်|ယူလာ|ယူလာခဲ့|
စစ်ဆေး|အတည်ပြု|ပြန်ကြား|ပြန်ပေး|လျှောက်ထား|တင်ရန်|အပ်နှံ|ပြင်ဆင်|ဖတ်|
ဒေါင်းလုဒ်|ပရင့်ထုတ်|လက်မှတ်ထိုး|ပါဝင်|တင်ပြ|လေ့ကျင့်|ဆက်သွယ်|အပ်ဒိတ်လုပ်|
နာမည်ပြောင်း|ပြင်|ပို့|တင်|ပေါင်း|

ဝင်ခွင့်လျှောက်ထား|စာရင်းပေးသွင်း|ဖောင်ဒေါင်းလုဒ်|ရလဒ်စစ်ဆေး|အချိန်ဇယားကြည့်|
သင်တန်းရွေးချယ်|စနစ်ဝင်ရောက်|လော့ဂ်အင်
""")


STUDENT_KEYWORDS = dedupe_list(STUDENT_KEYWORDS)
STUDENT_IMPORTANCE_HIGH = dedupe_list(STUDENT_IMPORTANCE_HIGH)
STUDENT_ACTION_KEYWORDS = dedupe_list(STUDENT_ACTION_KEYWORDS)


# ==========================================================
# Group-based student signals
# ==========================================================

STUDENT_SIGNAL_GROUPS = {
    "academic_identity": _kw("""
student|students|academic|university|college|school|campus|faculty|department|major|course|subject|
module|semester|term|year one|year two|first year|second year|third year|final year|
computer science|computer technology|information technology|degree programme|bachelor degree|master degree|doctoral degree|
ကျောင်းသား|ကျောင်းသူ|ပညာရေး|တက္ကသိုလ်|ကောလိပ်|ကျောင်း|ကင်ပတ်|ဌာန|မေဂျာ|ဘာသာရပ်|
နှစ်ဝက်|စမတ်စတာ|ပထမနှစ်|ဒုတိယနှစ်|တတိယနှစ်|နောက်ဆုံးနှစ်|ကွန်ပျူတာတက္ကသိုလ်|
ကွန်ပျူတာသိပ္ပံ|ကွန်ပျူတာနည်းပညာ|သတင်းအချက်အလက်နည်းပညာ
"""),

    "class_lecture": _kw("""
class|lecture|lesson|tutorial|lab|practical|classroom|online class|zoom class|google meet|
make up class|extra class|class cancelled|cancelled class|rescheduled class|lecture note|notes|handout|
teaching lab|learning management system|lms|
အတန်း|စာသင်ချိန်|သင်ခန်းစာ|လက်ချာ|လက်တွေ့ခန်း|အွန်လိုင်းအတန်း|စာသင်ခန်း|
အပိုအတန်း|အတန်းဖျက်|အတန်းရွှေ့|နုတ်စ်|စာရွက်|သင်ကြားရေးစနစ်|အွန်လိုင်းသင်ကြားရေး
"""),

    "schedule_time": _kw("""
schedule|timetable|calendar|academic calendar|class timetable|today|tomorrow|tmr|tmw|tonight|
this evening|next week|this week|morning|afternoon|evening|noon|pm|am|3 pm|4 pm|5 pm|
deadline time|date|time|slot|session|
အချိန်ဇယား|အတန်းချိန်ဇယား|စာသင်ချိန်ဇယား|ပညာရေးပြက္ခဒိန်|ယနေ့|ဒီနေ့|မနက်ဖြန်|
ညနေ|မနက်|နေ့လည်|နောက်အပတ်|အချိန်|ရက်စွဲ|ချိန်|အစည်းအဝေးချိန်
"""),

    "assignment_submission": _kw("""
assignment|homework|task|submit|submission|upload|deadline|due|due date|report|essay|paper|
worksheet|exercise|case study|lab report|individual assignment|group assignment|late submission|extension|
plagiarism|turnitin|google classroom|
အက်ဆိုင်းမန့်|အိမ်စာ|တာဝန်|တင်သွင်း|တင်ရန်|နောက်ဆုံးရက်|သတ်မှတ်ရက်|အစီရင်ခံစာ|
စာစီစာကုံး|လေ့ကျင့်ခန်း|အဖွဲ့လိုက်တာဝန်|နောက်ကျတင်သွင်း|အချိန်တိုး|ကူးယူမှု
"""),

    "exam_result": _kw("""
exam|examination|test|quiz|midterm|final|final exam|result|grade|marks|gpa|assessment|mock test|
oral test|viva|practical exam|exam room|seat plan|hall ticket|admit card|recheck|resit|retake|
entrance exam|check result|
စာမေးပွဲ|ဝင်ခွင့်စာမေးပွဲ|စမ်းသပ်စာမေးပွဲ|မစ်တမ်း|ဖိုင်နယ်|ရလဒ်|အောင်စာရင်း|
အမှတ်|ဂရိတ်|လက်တွေ့စာမေးပွဲ|စာမေးပွဲခန်း|ခုံနံပါတ်|ဝင်ခွင့်ကတ်|ပြန်စစ်|ပြန်ဖြေ|ရလဒ်စစ်ဆေး
"""),

    "meeting_discussion": _kw("""
meeting|meet|group meeting|team meeting|discussion|group discussion|project meeting|sync|briefing|
consultation|supervisor meeting|mentor meeting|standup|catch up|review meeting|
မီတင်|အစည်းအဝေး|တွေ့ဆုံ|ဆွေးနွေး|အဖွဲ့အစည်းအဝေး|ပရောဂျက်မီတင်|ညှိနှိုင်း|ဆရာနဲ့တွေ့|
ပြန်လည်သုံးသပ်မီတင်
"""),

    "presentation_project": _kw("""
presentation|present|slide|slides|ppt|pptx|presentation file|project|demo|viva|prototype|
poster|pitch|showcase|project report|project proposal|project title|final project|
ပရဆင်တေးရှင်း|တင်ပြ|စလိုက်|ပရောဂျက်|ပရဆင်တေးရှင်းဖိုင်|ဒီမို|ပိုစတာ|
နောက်ဆုံးပရောဂျက်|ပရောဂျက်အစီရင်ခံစာ|ပရောဂျက်ခေါင်းစဉ်
"""),

    "registration_payment": _kw("""
registration|register|enroll|enrollment|form|payment|fee|tuition|invoice|receipt|late fee|
admission|application form|student card|id card|course registration|exam registration|student registration|
student enrollment|admission requirements|register online|course register|apply admission|download form|
စာရင်းသွင်း|မှတ်ပုံတင်|ဖောင်|ငွေပေးချေ|ကျောင်းလခ|ကြေး|ပြေစာ|နောက်ကျကြေး|ဝင်ခွင့်|
လျှောက်လွှာ|ဝင်ခွင့်လျှောက်လွှာ|ကျောင်းသားကတ်|မှတ်ပုံတင်ကတ်|ဘာသာရပ်စာရင်းသွင်း|
စာမေးပွဲစာရင်းသွင်း|ကျောင်းသားမှတ်ပုံတင်|စာရင်းပေးသွင်း|ဖောင်ဒေါင်းလုဒ်
"""),

    "scholarship_internship": _kw("""
scholarship|grant|internship|internship application|training|workshop|competition|certificate|seminar|
webinar|bootcamp|career talk|job fair|volunteer|exchange program|fellowship|award|student awards|
application contest|science fair|quiz competition|
ပညာသင်ဆု|အလုပ်သင်|သင်တန်း|ဝပ်ရှော့|ပြိုင်ပွဲ|လက်မှတ်|ဆွေးနွေးပွဲ|
အွန်လိုင်းဆွေးနွေးပွဲ|အလုပ်အကိုင်ဆွေးနွေးပွဲ|စေတနာ့ဝန်ထမ်း|ဖလှယ်ရေးအစီအစဉ်|ဆု|
ကျောင်းသားဆု|သိပ္ပံပြပွဲ
"""),

    "attendance_leave": _kw("""
attendance|absent|absence|leave|excuse|cannot attend|can't attend|not coming|join|attend|
must attend|compulsory attendance|
တက်ရောက်မှု|မတက်ရောက်|ခွင့်|ခွင့်တိုင်|မလာနိုင်|မတက်နိုင်|တက်ရန်|ပါဝင်|မဖြစ်မနေတက်|
တက်ရောက်ရန်လိုအပ်
"""),

    "reply_action": _kw("""
reply|respond|response|confirm|check|bring|send|fill|complete|apply|prepare|read|review|
download|print|sign|contact|call|message me|dm me|let me know|inform|login|sign in|access lms|
view timetable|submit application|
ပြန်ပေး|ပြန်ကြား|အကြောင်းပြန်|အတည်ပြု|စစ်ဆေး|ယူလာ|ယူလာခဲ့|ပို့|ဖြည့်|ပြီးအောင်လုပ်|
လျှောက်ထား|ပြင်ဆင်|ဖတ်|ပြန်ကြည့်|ဒေါင်းလုဒ်|ပရင့်ထုတ်|လက်မှတ်ထိုး|ဆက်သွယ်|ပြောပေး|
အသိပေး|ဝင်ခွင့်လျှောက်ထား|အချိန်ဇယားကြည့်|စနစ်ဝင်ရောက်|လော့ဂ်အင်
"""),

    "official_notice": _kw("""
notice|announcement|official|admin|office|dean|rector|teacher|lecturer|professor|coordinator|
department office|student affairs|registrar|academic office|important announcement|official announcement|
ကြေညာချက်|အသိပေးစာ|တရားဝင်|ရုံး|ဆရာ|ဆရာမ|ပါမောက္ခ|ဌာနမှူး|ညှိနှိုင်းရေးမှူး|
ဌာနရုံး|ကျောင်းသားရေးရာ|ပညာရေးရုံး|အရေးကြီးကြေညာချက်
"""),

    "materials_files": _kw("""
file|files|attachment|document|pdf|docx|excel|spreadsheet|image|photo|presentation file|slides|
notes|lecture notes|book|ebook|handbook|academic guide|curriculum|syllabus|course syllabus|
ဖိုင်|စာရွက်စာတမ်း|ပူးတွဲဖိုင်|စာအုပ်|နုတ်စ်|လက်ချာနုတ်စ်|ဓာတ်ပုံ|ပုံ|pdf|word|excel|
သင်ရိုး|သင်ရိုးညွှန်းတမ်း
"""),

    "school_admin_process": _kw("""
library|clearance|hostel|male hostel|female hostel|dormitory|uniform|student id|id card|transcript|
recommendation letter|certificate|graduation|convocation|orientation|graduation ceremony|campus facilities|
campus life|campus tour|library management system|e-library|
စာကြည့်တိုက်|ရှင်းလင်းစာရင်း|အဆောင်|ယူနီဖောင်း|ကျောင်းသားနံပါတ်|ကျောင်းသားကတ်|မှတ်တမ်း|
ထောက်ခံစာ|လက်မှတ်|ဘွဲ့ယူ|ဘွဲ့နှင်းသဘင်|မိတ်ဆက်ပွဲ|ကျောင်းသားလှုပ်ရှားမှု
"""),

    "casual_student_context": _kw("""
bro|sis|friend|group|our group|team|classmate|mate|guys|everyone|leader|
အဖွဲ့|သူငယ်ချင်း|ကလပ်စ်မိတ်|အဖွဲ့သား|အဖွဲ့ခေါင်းဆောင်|အားလုံး|သူငယ်ချင်းတို့
"""),

    "university_domains": _kw("""
ucsy|ucsm|uit|ucstt|ucsy.edu.mm|ucsm.edu.mm|uit.edu.mm|ucstt.edu.mm|edu.mm|student.edu.mm|
university of computer studies yangon|university of computer studies mandalay|
university of information technology|university of computer studies thaton
"""),
}


# ==========================================================
# Non-student signal groups
# ==========================================================

NON_STUDENT_SIGNAL_GROUPS = {
    "shopping_sales": _kw("""
shop|phone shop|mobile shop|computer shop|store|sales|sale|discount|bundle|promotion|promo|
offer|price|buy|sell|product|product presentation|sales presentation|product demo|laptop discount|
phone discount|mouse|keyboard|gaming mouse|keyboard bundle|ticket booking|ticket|booking|cashback|
voucher|coupon|preorder|order now|limited offer|flash sale|black friday|clearance sale|
ဆိုင်|ဖုန်းဆိုင်|လက်တော့ဆိုင်|ကွန်ပျူတာဆိုင်|လျှော့စျေး|စျေးလျှော့|ပစ္စည်း|ကုန်ပစ္စည်း|
ဝယ်|ရောင်း|ပရိုမိုးရှင်း|အော်ဒါ|ဘွတ်ကင်|လက်မှတ်|ကူပွန်|ဗောက်ချာ|စျေးနှုန်း|အထူးလျှော့စျေး
"""),

    "explicit_not_school": _kw("""
school presentation မဟုတ်ဘူး|school မဟုတ်ဘူး|university မဟုတ်ဘူး|class မဟုတ်ဘူး|
assignment မဟုတ်ဘူး|exam မဟုတ်ဘူး|school project မဟုတ်ဘူး|university project မဟုတ်ဘူး|
student project မဟုတ်ဘူး|school, class, assignment ဘာမှမဟုတ်ဘူး|not school|not university|
not class|not assignment|not exam|not a school presentation|not university related|not student related|
not academic|not academic related|sales presentation ပဲ|product presentation ပဲ|ဆိုင်က sales presentation|
ဆိုင်က product presentation|ကျောင်းကိစ္စမဟုတ်ဘူး|တက္ကသိုလ်ကိစ္စမဟုတ်ဘူး|စာသင်ခန်းကိစ္စမဟုတ်ဘူး|
အက်ဆိုင်းမန့်မဟုတ်ဘူး|စာမေးပွဲမဟုတ်ဘူး|ကျောင်း project မဟုတ်ဘူး|ကျောင်းသား project မဟုတ်ဘူး|
ပညာရေးကိစ္စမဟုတ်ဘူး
"""),

    "entertainment_personal": _kw("""
movie|cinema|film|gaming|game|tournament|birthday|party|food|restaurant|bubble tea|
coffee shop|cafe|concert|music show|football match|trip|travel|hangout|date|shopping|mall|gym|
boxing class|fitness class|dance class|karaoke|picnic|
ရုပ်ရှင်|ဂိမ်း|ပြိုင်ပွဲဂိမ်း|မွေးနေ့|ပါတီ|စား|သောက်|စားသောက်ဆိုင်|လက်ဖက်ရည်|ကော်ဖီဆိုင်|
ဖျော်ဖြေပွဲ|ဘောလုံးပွဲ|ခရီး|လျှောက်လည်|စျေးဝယ်|မောလ်|ဂျင်မ်|ဘောက်ဆင်|ပျော်ပွဲစား
"""),

    "office_client": _kw("""
client|company|office|work project|client project|office project|boss|manager|customer|business|
invoice|quotation|purchase order|payment approval|company meeting|office meeting|client demo|customer demo|
sales team|marketing team|work deadline|business meeting|staff meeting|
ကုမ္ပဏီ|ရုံး|အလုပ်ကိစ္စ|အလုပ် project|ရုံး project|မန်နေဂျာ|ဘော့စ်|စီးပွားရေး|
ဘောင်ချာ|ငွေတောင်းခံလွှာ|ကုမ္ပဏီ meeting|ရုံး meeting|အလုပ် deadline|ဝန်ထမ်း meeting
"""),
}


# =========================
# Regex patterns
# =========================

MYANMAR_CHAR_PATTERN = re.compile(r"[\u1000-\u109F\uAA60-\uAA7F]")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w+\b")
EXTRA_SPACE_PATTERN = re.compile(r"[ \t]+")


# =========================
# Text helpers
# =========================

def contains_myanmar(text):
    return bool(text and MYANMAR_CHAR_PATTERN.search(str(text)))


def normalize_for_matching(text):
    if not text:
        return ""

    text = str(text).lower()
    text = text.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    text = text.replace("_", " ").replace("-", " ").replace("/", " ").replace("\\", " ")
    text = re.sub(r"[^\w\s\u1000-\u109F\uAA60-\uAA7F]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def polish_burmese_text(text):
    if text is None:
        return text

    text = str(text).strip()

    replacements = {
        "ပေးပိုသူ": "ပေးပို့သူ",
        "ပေးပို": "ပေးပို့",
        "အချိုသော": "အချို့သော",
        "သောကြောင့်": "သောကြောင့်",
        "ကြောင့်": "ကြောင့်",
        "မဖော်ပြထားပါ။။": "မဖော်ပြထားပါ။",
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_mm(value, default="မဖော်ပြထားပါ"):
    if value is None:
        return default

    value = str(value).strip()
    if value in ["", "None", "none", "null"]:
        return default

    return polish_burmese_text(value)


def make_separator():
    return "━━━━━━━━━━━━━━"


def sanitize_header_value(value):
    if value is None:
        return ""

    value = str(value).replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", value).strip()


def sanitize_email_address(value):
    if value is None:
        return ""

    return str(value).replace("\r", "").replace("\n", "").strip()


def clean_text_for_nlp(text):
    if not text:
        return ""

    text = str(text)
    text = URL_PATTERN.sub(" [URL] ", text)
    text = EMAIL_PATTERN.sub(" [EMAIL] ", text)
    text = EXTRA_SPACE_PATTERN.sub(" ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("[Email body truncated]", "")
    return text.strip()


def smart_truncate(text, limit=6000):
    if not text:
        return ""

    if len(text) <= limit:
        return text

    return text[:limit] + "\n[Truncated]"


def split_sentences(text):
    if not text:
        return []

    text = clean_text_for_nlp(text)

    if contains_myanmar(text):
        parts = re.split(r"(?<=[။.!?])\s+|[\n]+|(?<=၊)\s*", text)
    else:
        parts = re.split(r"(?<=[.!?])\s+|\n+", text)

    return [p.strip(" \t\r\n-•*") for p in parts if len(p.strip()) >= 8]


def clean_summary_for_display(summary, max_sentences=4):
    summary = safe_mm(summary, "အနှစ်ချုပ် မဖော်ပြထားပါ။")

    for label in [
        "Summary:", "Summary:\n",
        "အနှစ်ချုပ်:", "အနှစ်ချုပ်:\n",
        "Main point:", "Main Point:",
    ]:
        summary = summary.replace(label, "")

    lines = []
    for line in summary.splitlines():
        line = line.strip()
        line = re.sub(r"^[•\-\*\u2022●▪▫]+\s*", "", line)
        line = re.sub(r"^\d+[.)]\s*", "", line)
        line = re.sub(r"^[၁၂၃၄၅၆၇၈၉၀]+[။.)]\s*", "", line)
        if line:
            lines.append(line)

    summary = " ".join(lines)
    summary = re.sub(r"\s+", " ", summary).strip()
    summary = polish_burmese_text(summary)

    sentences = re.split(r"(?<=[။.!?])\s+", summary)
    sentences = [s.strip() for s in sentences if len(s.strip()) >= 5]

    paragraph = " ".join(sentences[:max_sentences]).strip() if sentences else summary

    if contains_myanmar(paragraph) and not paragraph.endswith(("။", ".", "!", "?")):
        paragraph += "။"

    return paragraph or "အနှစ်ချုပ် မဖော်ပြထားပါ။"


def format_summary_section_mm(summary):
    summary = clean_summary_for_display(summary)

    if not summary or summary == "အနှစ်ချုပ် မဖော်ပြထားပါ။":
        return "📝 အနှစ်ချုပ်\nအကြောင်းအရာအပြည့်အစုံ မဖော်ပြထားပါ။"

    return f"📝 အနှစ်ချုပ်\n{summary}"


def extractive_summary_nlp(text, max_sentences=4):
    if not text:
        return "Email အကြောင်းအရာ မတွေ့ပါ။"

    sentences = split_sentences(text)

    if not sentences:
        return smart_truncate(text, 500)

    if len(sentences) <= max_sentences:
        return clean_summary_for_display(" ".join(sentences), max_sentences)

    scored = []
    all_keywords = STUDENT_KEYWORDS + STUDENT_IMPORTANCE_HIGH + STUDENT_ACTION_KEYWORDS

    for idx, sentence in enumerate(sentences):
        lower = sentence.lower()
        score = 0

        for kw in all_keywords:
            if kw.lower() in lower:
                score += 3

        if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", sentence):
            score += 4

        if re.search(r"\b\d{1,2}\s?(am|pm)\b", sentence, flags=re.IGNORECASE):
            score += 4

        score += max(0, 3 - idx)
        scored.append((score, idx, sentence))

    top = sorted(scored, key=lambda x: x[0], reverse=True)[:max_sentences]
    top = sorted(top, key=lambda x: x[1])

    return clean_summary_for_display(" ".join(x[2] for x in top), max_sentences)


def extract_deadline_local(text):
    if not text:
        return "မဖော်ပြထားပါ"

    text = clean_text_for_nlp(text)
    matches = []

    uncertain_deadline_phrases = [
        "not sure", "i’m not sure", "i'm not sure", "not official",
        "is that official", "deadline changes?", "deadline change?",
        "heard something", "maybe", "might", "could be", "i heard",
        "မသေချာ", "တရားဝင်မဟုတ်",
    ]

    date_patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
        r"\b\d{1,2}\s?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s?\d{2,4}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s?\d{1,2},?\s?\d{2,4}\b",
        r"\b\d{1,2}\s?(am|pm)\b",
        r"\b(today|tomorrow|tonight)\b",
        r"ဒီနေ့",
        r"ယနေ့",
        r"မနက်ဖြန်",
        r"ည",
        r"မနက်",
    ]

    deadline_keywords = [
        "deadline", "due", "submit by", "before", "until",
        "today", "tomorrow", "tonight",
        "နောက်ဆုံးထား", "သတ်မှတ်ရက်", "အပ်ရမည့်ရက်",
        "တင်သွင်းရမည့်ရက်", "မတိုင်မီ", "ယနေ့", "ဒီနေ့", "မနက်ဖြန်",
    ]

    for sentence in split_sentences(text):
        lower = sentence.lower()

        if any(p in lower for p in uncertain_deadline_phrases):
            continue

        has_deadline_keyword = any(k.lower() in lower for k in deadline_keywords)
        has_date = any(re.search(pattern, sentence, flags=re.IGNORECASE) for pattern in date_patterns)

        if has_deadline_keyword and has_date:
            cleaned = polish_burmese_text(sentence)

            if len(cleaned) > 180:
                cleaned = cleaned[:180].strip() + "..."

            if cleaned not in matches:
                matches.append(cleaned)

    return "၊ ".join(matches[:3]) if matches else "မဖော်ပြထားပါ"


def extract_action_item_local(text):
    if not text:
        return "မရှိပါ"

    sentences = split_sentences(text)

    weak_phrases = [
        "i just wanted",
        "check a few things",
        "also share",
        "not sure",
        "maybe",
        "heard something",
        "wanted to check",
        "just wanted to check",
    ]

    found_actions = []

    for sentence in sentences:
        lower = sentence.lower()

        if any(w in lower for w in weak_phrases):
            continue

        if any(k.lower() in lower for k in STUDENT_ACTION_KEYWORDS):
            cleaned = clean_summary_for_display(sentence, max_sentences=1)
            if cleaned and cleaned not in found_actions:
                found_actions.append(cleaned)

    if not found_actions:
        return "မရှိပါ"

    return "၊ ".join(found_actions[:3])


# =========================
# Optional student scoring helpers
# =========================

def count_keyword_hits(text, keywords):
    normalized = normalize_for_matching(text)
    hits = []

    for kw in keywords:
        kw_norm = normalize_for_matching(kw)
        if kw_norm and kw_norm in normalized:
            hits.append(kw)

    return dedupe_list(hits)


def is_trusted_student_domain(text):
    if not text:
        return False

    lower = str(text).lower()
    return any(domain.lower() in lower for domain in TRUSTED_STUDENT_DOMAINS)


def get_student_signal_hits(text):
    hits = {}

    for group_name, keywords in STUDENT_SIGNAL_GROUPS.items():
        group_hits = count_keyword_hits(text, keywords)
        if group_hits:
            hits[group_name] = group_hits

    return hits


def get_non_student_signal_hits(text):
    hits = {}

    for group_name, keywords in NON_STUDENT_SIGNAL_GROUPS.items():
        group_hits = count_keyword_hits(text, keywords)
        if group_hits:
            hits[group_name] = group_hits

    return hits


def student_relevance_score(text, source_text=""):
    if not text and not source_text:
        return 0

    full_text = f"{source_text}\n{text}"
    score = 0

    student_hits = get_student_signal_hits(full_text)
    non_student_hits = get_non_student_signal_hits(full_text)

    for group_name, hits in student_hits.items():
        if group_name in ["official_notice", "registration_payment", "exam_result"]:
            score += len(hits) * 3
        elif group_name in ["university_domains", "academic_identity"]:
            score += len(hits) * 4
        else:
            score += len(hits) * 2

    for group_name, hits in non_student_hits.items():
        if group_name == "explicit_not_school":
            score -= len(hits) * 6
        else:
            score -= len(hits) * 3

    if is_trusted_student_domain(full_text):
        score += 8

    if any(k.lower() in normalize_for_matching(full_text) for k in STUDENT_IMPORTANCE_HIGH):
        score += 5

    return score


def is_student_related(text, source_text="", threshold=4):
    return student_relevance_score(text, source_text) >= threshold