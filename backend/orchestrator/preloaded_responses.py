"""
National University AI Assistant - Preloaded Instant Response Engine
Pre-compiled, rich responses with official links, citations, and interactive chips for zero-latency (<1ms) execution.
"""

import re
from typing import Optional, Dict, Any
from backend.models.schemas import ChatResponse, SourceCitation

TOKEN_ID_REGEX = re.compile(r'\b(NU-\d{4}-\d{6})\b', re.IGNORECASE)

# Pre-compiled Citation Cards
CITATIONS_ADMISSION = [
    SourceCitation(title="জাতীয় বিশ্ববিদ্যালয় ভর্তি পোর্টাল", url="http://app11.nu.edu.bd/", date="অফিসিয়াল পোর্টাল"),
    SourceCitation(title="অনলাইন ভর্তি নির্দেশিকা", url="http://app11.nu.edu.bd/notice", date="সার্কুলার")
]

CITATIONS_EMS = [
    SourceCitation(title="EMS স্টুডেন্ট পোর্টাল", url="https://ems.nu.ac.bd/", date="অফিসিয়াল সেবা"),
    SourceCitation(title="ফরম পূরণ নোটিশ বোর্ড", url="https://www.nu.ac.bd/recent-notices.php", date="রুটিন")
]

CITATIONS_ERP_SERVICES = [
    SourceCitation(title="জাতীয় বিশ্ববিদ্যালয় স্টুডেন্ট ERP সার্ভিসেস পোর্টাল", url="http://103.113.200.68/nu-app/", date="ERP অনলাইন সেবা"),
    SourceCitation(title="জাতীয় বিশ্ববিদ্যালয় অনলাইন সার্ভিস পোর্টাল", url="http://103.113.200.68/nu-app/", date="স্টুডেন্ট লগইন"),
    SourceCitation(title="সোনালী সেবা ই-পেমেন্ট গেটওয়ে", url="https://www.nu.ac.bd/", date="অনলাইন পেমেন্ট")
]

CITATIONS_RESULTS = [
    SourceCitation(title="জাতীয় বিশ্ববিদ্যালয় ফলাফল আর্কাইভ", url="https://results.nu.ac.bd/", date="ফলাফল পোর্টাল"),
    SourceCitation(title="রেজাল্ট সার্ভার ২", url="http://103.113.200.68/nu-app/search.php", date="বিকল্প সার্ভার")
]

CITATIONS_GENERAL = [
    SourceCitation(title="জাতীয় বিশ্ববিদ্যালয় মূল ওয়েবসাইট", url="https://www.nu.ac.bd/", date="অফিসিয়াল পোর্টাল"),
    SourceCitation(title="সাম্প্রতিক নোটিশ ও অফিস আদেশ", url="https://www.nu.ac.bd/recent-notices.php", date="সার্কুলার"),
    SourceCitation(title="ভর্তি ও রেজিস্ট্রেশন পোর্টাল", url="http://app11.nu.edu.bd/", date="ভর্তি শাখা"),
    SourceCitation(title="EMS ও ফরম পূরণ পোর্টাল", url="https://ems.nu.ac.bd/", date="পরীক্ষা শাখা")
]

# 1. Welcome & General Overview Message (Exact rich layout from Master UI)
WELCOME_REPLY = """জাতীয় বিশ্ববিদ্যালয়ের (National University of Bangladesh) শিক্ষা বিষয়ক যেকোনো সহায়তার জন্য আপনার নির্দিষ্ট প্রশ্নটি করুন। আপনাকে কীভাবে সহায়তা করা যেতে পারে তার একটি সংক্ষিপ্ত তালিকা নিচে দেওয়া হলো:

### ১. ভর্তি সংক্রান্ত তথ্য (Admissions)
• **কোর্সসমূহ:** অনার্স (সম্মান), ডিগ্রি (পাস), মাস্টার্স ও প্রফেশনাল কোর্স।
• **ভর্তি প্রক্রিয়া:** এসএসসি ও এইচএসসি ফলাফলের ভিত্তিতে সরাসরি অনলাইনে আবেদন সম্পন্ন করতে হয়।
• **অফিসিয়াল লিংক:** [জাতীয় বিশ্ববিদ্যালয় ভর্তি পোর্টাল](http://app11.nu.edu.bd/)

### ২. পরীক্ষা ও ফরম পূরণ (Form Fill-Up & EMS)
• **পরীক্ষার ফরম পূরণ:** অনলাইনে ফরম পূরণ সম্পন্ন করে স্ব-স্ব কলেজে ফি সহ জমা দিতে হয়।
• **ইএমএস অ্যাকাউন্ট সমস্যা:** একাউন্ট ব্লক বা পাসওয়ার্ড ভুলে গেলে [EMS পোর্টালে](https://ems.nu.ac.bd/) শিক্ষার্থী তথ্য যাচাই করে রিসেট সুবিধা পাওয়া যায়।
• **অফিসিয়াল লিংক:** [ফরম পূরণ ও ইএমএস পোর্টাল](https://ems.nu.ac.bd/)

### ৩. পরীক্ষার ফলাফল (Results)
• **সিজিপিএ (CGPA) ও গ্রেডিং:** বছরভিত্তিক ফলাফল জানতে রেজিস্ট্রেশন/রোল নম্বর ব্যবহার করুন।
• **নিরাপদ চেক লিংক:** [ফলাফল পোর্টাল](https://results.nu.ac.bd/) অথবা যেকোনো মোবাইল থেকে SMS করুন:
  `NU <space> DEG/HONS/MAT <space> Roll/Reg No` লিখে পাঠান **16222** নম্বরে।

### ৪. একাডেমিক নোটিশ ও সার্কুলার
• সময়সূচি, সংশোধিত রুটিন ও জরুরি নির্দেশনার জন্য সর্বদা অফিসিয়াল নোটিশ বোর্ড অনুসরণ করুন।
• **অফিসিয়াল লিংক:** [জাতীয় বিশ্ববিদ্যালয় নোটিশ বোর্ড](https://www.nu.ac.bd/recent-notices.php)

### ৫. প্রশাসনিক ও দাপ্তরিক যোগাযোগ
• [রেজিস্ট্রার দপ্তর](https://www.nu.ac.bd/) • [পরীক্ষা নিয়ন্ত্রক দপ্তর](https://www.nu.ac.bd/)
• [আইসিটি দপ্তর](https://www.nu.ac.bd/) • [উপাচার্য দপ্তর](https://www.nu.ac.bd/)

আপনার নির্দিষ্ট কোনো বিষয়, পরীক্ষা বা ভর্তি সম্পর্কিত প্রশ্ন থাকলে বিস্তারিত জানান।"""

# 1b. Main Menu Grid (Square Shape Cards that Fit the Screen with Colorful Icons)
MAIN_MENU_REPLY = """<div class="space-y-3 font-sans text-left">
  <div class="p-3.5 bg-gradient-to-r from-emerald-800 to-teal-900 text-white rounded-2xl shadow-xs">
    <div class="text-[10px] uppercase tracking-wider text-emerald-200 font-bold">জাতীয় বিশ্ববিদ্যালয় বাংলাদেশ (nu.ac.bd)</div>
    <h3 class="text-base font-bold text-white mt-0.5">🏛️ মূল একাডেমিক সেবা মেনু</h3>
    <p class="text-xs text-emerald-100 mt-1">নিচের যেকোনো সেবা বা পরীক্ষার তথ্যে ক্লিক করে সরাসরি জেনে নিন:</p>
  </div>

  <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
    
    <!-- Card 1: Honours -->
    <div onclick="handleExamCategoryClick('Honours')" class="group p-3 rounded-2xl border border-blue-200 bg-gradient-to-b from-blue-50/60 to-white hover:from-blue-100 hover:to-blue-50 hover:border-blue-500 hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center text-xl shadow-xs group-hover:scale-110 transition-transform">
        📘
      </div>
      <div>
        <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:text-blue-700 transition">অনার্স পরীক্ষা</h4>
        <p class="text-[10px] text-slate-500">১ম, ২য়, ৩য়, ৪র্থ বর্ষ</p>
      </div>
    </div>

    <!-- Card 2: Degree Pass -->
    <div onclick="handleExamCategoryClick('Degree Pass')" class="group p-3 rounded-2xl border border-indigo-200 bg-gradient-to-b from-indigo-50/60 to-white hover:from-indigo-100 hover:to-indigo-50 hover:border-indigo-500 hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center text-xl shadow-xs group-hover:scale-110 transition-transform">
        📗
      </div>
      <div>
        <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:text-indigo-700 transition">ডিগ্রি পরীক্ষা</h4>
        <p class="text-[10px] text-slate-500">১ম, ২য়, ৩য় বর্ষ</p>
      </div>
    </div>

    <!-- Card 3: Master's -->
    <div onclick="handleExamCategoryClick('Master\\'s')" class="group p-3 rounded-2xl border border-purple-200 bg-gradient-to-b from-purple-50/60 to-white hover:from-purple-100 hover:to-purple-50 hover:border-purple-500 hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="w-10 h-10 rounded-xl bg-purple-600 text-white flex items-center justify-center text-xl shadow-xs group-hover:scale-110 transition-transform">
        📙
      </div>
      <div>
        <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:text-purple-700 transition">মাস্টার্স পরীক্ষা</h4>
        <p class="text-[10px] text-slate-500">শেষ পর্ব ও প্রিলি</p>
      </div>
    </div>

    <!-- Card 4: Professional -->
    <div onclick="handleExamCategoryClick('Professional')" class="group p-3 rounded-2xl border border-teal-200 bg-gradient-to-b from-teal-50/60 to-white hover:from-teal-100 hover:to-teal-50 hover:border-teal-500 hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center text-xl shadow-xs group-hover:scale-110 transition-transform">
        🎓
      </div>
      <div>
        <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:text-teal-700 transition">প্রফেশনাল পরীক্ষা</h4>
        <p class="text-[10px] text-slate-500">১ম - ৮ম সেমিস্টার</p>
      </div>
    </div>

    <!-- Card 5: Admission -->
    <div onclick="sendQuickQuestion('অনার্স ১ম বর্ষের ভর্তি বিজ্ঞপ্তি ও নিয়মাবলি')" class="group p-3 rounded-2xl border border-emerald-200 bg-gradient-to-b from-emerald-50/60 to-white hover:from-emerald-100 hover:to-emerald-50 hover:border-emerald-500 hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center text-xl shadow-xs group-hover:scale-110 transition-transform">
        🎯
      </div>
      <div>
        <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:text-emerald-700 transition">অনার্স ভর্তি তথ্য</h4>
        <p class="text-[10px] text-slate-500">মেধা তালিকা ও সার্কুলার</p>
      </div>
    </div>

    <!-- Card 6: Routine -->
    <div onclick="sendQuickQuestion('সর্বশেষ পরীক্ষার রুটিন ও নোটিশ')" class="group p-3 rounded-2xl border border-cyan-200 bg-gradient-to-b from-cyan-50/60 to-white hover:from-cyan-100 hover:to-cyan-50 hover:border-cyan-500 hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="w-10 h-10 rounded-xl bg-cyan-600 text-white flex items-center justify-center text-xl shadow-xs group-hover:scale-110 transition-transform">
        📅
      </div>
      <div>
        <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:text-cyan-700 transition">পরীক্ষার রুটিন</h4>
        <p class="text-[10px] text-slate-500">সকল শিক্ষাবর্ষ</p>
      </div>
    </div>

    <!-- Card 7: Certificate -->
    <div onclick="sendQuickQuestion('অনলাইনে মূল সার্টিফিকেট উত্তোলনের নিয়ম ও ফি কত?')" class="group p-3 rounded-2xl border border-violet-200 bg-gradient-to-b from-violet-50/60 to-white hover:from-violet-100 hover:to-violet-50 hover:border-violet-500 hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="w-10 h-10 rounded-xl bg-violet-600 text-white flex items-center justify-center text-xl shadow-xs group-hover:scale-110 transition-transform">
        📜
      </div>
      <div>
        <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:text-violet-700 transition">সার্টিফিকেট উত্তোলন</h4>
        <p class="text-[10px] text-slate-500">ফি ও উত্তোলনের নিয়ম</p>
      </div>
    </div>

    <!-- Card 8: EMS -->
    <div onclick="sendQuickQuestion('ডিগ্রি ও অনার্স ফরম পূরণের নিয়মাবলি')" class="group p-3 rounded-2xl border border-amber-200 bg-gradient-to-b from-amber-50/60 to-white hover:from-amber-100 hover:to-amber-50 hover:border-amber-500 hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="w-10 h-10 rounded-xl bg-amber-600 text-white flex items-center justify-center text-xl shadow-xs group-hover:scale-110 transition-transform">
        📝
      </div>
      <div>
        <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:text-amber-700 transition">ফরম পূরণ (EMS)</h4>
        <p class="text-[10px] text-slate-500">সময়সীমা ও ফি জমা</p>
      </div>
    </div>

    <!-- Card 9: TC -->
    <div onclick="sendQuickQuestion('কলেজ ছাড়পত্র (TC) নেওয়ার উপায় কি?')" class="group p-3 rounded-2xl border border-rose-200 bg-gradient-to-b from-rose-50/60 to-white hover:from-rose-100 hover:to-rose-50 hover:border-rose-500 hover:shadow-md transition-all cursor-pointer flex flex-col items-center justify-center text-center gap-1.5 aspect-square sm:aspect-auto sm:min-h-[110px]">
      <div class="w-10 h-10 rounded-xl bg-rose-600 text-white flex items-center justify-center text-xl shadow-xs group-hover:scale-110 transition-transform">
        🏫
      </div>
      <div>
        <h4 class="font-bold text-slate-900 text-xs sm:text-sm group-hover:text-rose-700 transition">কলেজ টিসি (TC)</h4>
        <p class="text-[10px] text-slate-500">অনলাইন ছাড়পত্র</p>
      </div>
    </div>

  </div>
</div>"""

# 2. Preloaded Admissions Overview
ADMISSION_REPLY = """### 🎓 জাতীয় বিশ্ববিদ্যালয় ভর্তি নির্দেশিকা ও তথ্য (Admissions)

জাতীয় বিশ্ববিদ্যালয়ের অধীনে সকল স্নাতক (সম্মান), পাস ও স্নাতকোত্তর কোর্সে মেধা তালিকার ভিত্তিতে শিক্ষার্থী ভর্তি করা হয়:

1. **অনার্স ১ম বর্ষ (Honours 1st Year):**
   - **যোগ্যতা:** এসএসসি ও এইচএসসি পরীক্ষায় নির্দিষ্ট ন্যূনতম জিপিএ (মানবিকে মোট ৬.৫, বিজ্ঞান ও ব্যবসায় শিক্ষায় ৭.০)।
   - **আবেদন প্রক্রিয়া:** [ভর্তি পোর্টালে](http://app11.nu.edu.bd/) প্রাথমিক আবেদন ফরম পূরণ করে কলেজ কর্তৃক নির্ধারিত ফি রকেট/বিকাশ/মোবাইল ব্যাংকিংয়ের মাধ্যমে জমা দিতে হয়।
2. **ডিগ্রি (পাস) কোর্স:**
   - ৩ বছর মেয়াদী বিএ/বিএসএস/বিবিএস/বিএসসি কোর্সে আবেদন কার্যক্রম সার্কুলার অনুযায়ী পরিচালিত হয়।
3. **মাস্টার্স ও প্রফেশনাল কোর্স:**
   - প্রিলিমিনারি ও মাস্টার্স ফাইনাল কোর্সে অনলাইনে আবেদন গ্রহণ করা হয়।

👉 **ভর্তি সংক্রান্ত অফিসিয়াল পোর্টাল:** [app11.nu.edu.bd](http://app11.nu.edu.bd/)"""

# 3. Preloaded Examination & Routine
EXAM_REPLY = """### 📝 পরীক্ষা ও রুটিন সংক্রান্ত তথ্য (Examinations & Routines)

জাতীয় বিশ্ববিদ্যালয়ের সকল পরীক্ষার রুটিন, কেন্দ্র তালিকা ও সংশোধিত বিজ্ঞপ্তি সংক্রান্ত জরুরি তথ্য:

1. **পরীক্ষার রুটিন প্রকাশ:** সকল বর্ষের পরীক্ষার রুটিন অফিসিয়াল নোটিশ বোর্ডে পিডিএফ আকারে প্রকাশিত হয়।
2. **প্রবেশপত্র (Admit Card):** পরীক্ষা শুরুর সাধারণত ৩-৭ দিন পূর্বে স্ব-স্ব কলেজ অধ্যক্ষের মাধ্যমে সিল ও স্বাক্ষরযুক্ত প্রবেশপত্র বিতরণ করা হয়।
3. **পরীক্ষার নিয়মাবলী:** প্রবেশপত্র এবং রেজিস্ট্রেশন কার্ড অবশ্যই পরীক্ষার হলে সাথে রাখতে হবে।

👉 **পরীক্ষার সর্বশেষ নোটিশ ও রুটিন দেখুন:** [nu.ac.bd/recent-notices.php](https://www.nu.ac.bd/recent-notices.php)"""

# 4. Preloaded Results & SMS System
RESULTS_REPLY = """### 📊 পরীক্ষার ফলাফল ও সিজিপিএ জানার নিয়ম (Results)

জাতীয় বিশ্ববিদ্যালয়ের ফলাফল দ্রুত ও নির্ভুলভাবে জানার দুটি পদ্ধতি রয়েছে:

1. **অনলাইন পোর্টাল (Web Portal):**
   - [results.nu.ac.bd](https://results.nu.ac.bd/) ভিজিট করে আপনার রোল এবং রেজিস্ট্রেশন নম্বর দিয়ে বছর নির্বাচন করুন।
2. **এসএমএস (SMS) এর মাধ্যমে দ্রুত ফলাফল:**
   - মেসেজ অপশনে গিয়ে লিখুন:
     - **অনার্স:** `NU HONS <Roll/Registration No>`
     - **ডিগ্রি:** `NU DEG <Roll/Registration No>`
     - **মাস্টার্স:** `NU MAT <Roll/Registration No>`
   - পাঠিয়ে দিন **16222** নম্বরে (যেকোনো মোবাইল অপারেটর থেকে)।

3. **ফলাফল পুনর্নিরীক্ষণ (Rescrutiny):**
   - ফলাফল প্রকাশের ৩০ দিনের মধ্যে সোনালী সেবার মাধ্যমে অনলাইনে ফি জমা দিয়ে আবেদন করা যায়।"""

# 5. Preloaded Form Fill-Up & EMS
EMS_REPLY = """### 💻 পরীক্ষার ফরম পূরণ ও ইএমএস পোর্টাল নির্দেশিকা (Exam Form Fill-Up & EMS)

জাতীয় বিশ্ববিদ্যালয়ের অনার্স, ডিগ্রি, মাস্টার্স ও প্রফেশনাল পরীক্ষার ফরম পূরণ কার্যক্রম সম্পূর্ণ ডিজিটালি **EMS (Exam Management System)** পোর্টালের মাধ্যমে পরিচালিত হয়:

#### ১. সরাসরি অফিসিয়াল লগইন লিংক:
👉 **স্টুডেন্ট লগইন পোর্টাল:** [https://ems.nu.ac.bd/student-login](https://ems.nu.ac.bd/student-login)

#### ২. ফরম পূরণের পর্যায়ক্রমিক সঠিক ধাপসমূহ:
1. **লগইন করুন:** আপনার ইন্টারনেট ব্রাউজার থেকে সরাসরি [https://ems.nu.ac.bd/student-login](https://ems.nu.ac.bd/student-login) লিংকে প্রবেশ করুন।
2. **ইউজার ক্রেডেনশিয়াল:** আপনার রেজিস্ট্রেশন নম্বর (Registration No) এবং নির্ধারিত শিক্ষাবর্ষ (Session) ইনপুট দিয়ে ড্যাশবোর্ডে প্রবেশ করুন।
3. **কোর্স ও সাবজেক্ট কোড যাচাই:** আপনার সংশ্লিষ্ট বর্ষের আবশ্যিক (Compulsory) এবং ঐচ্ছিক/ইলেকটিভ (Elective) বিষয় কোডগুলো সিলেবাস অনুযায়ী সঠিকভাবে নির্বাচিত আছে কি না নিশ্চিত করুন।
4. **ফরম সাবমিট ও পে-স্লিপ প্রিন্ট:** তথ্য সঠিক থাকলে আবেদন সাবমিট করুন এবং আবেদন ফরমের প্রিন্ট কপি (Student Application Form) ও সোনালী সেবা পে-স্লিপ ডাউনলোড করে প্রিন্ট করুন।
5. **ফি প্রদান:** কলেজ নির্ধারিত সময়সীমার মধ্যে সোনালী ব্যাংকের মাধ্যমে অথবা কলেজের নির্দেশিত মোবাইল ব্যাংকিং/অনলাইন গেটওয়েতে পরীক্ষার ফি জমা দিন।
6. **কলেজে হার্ডকপি জমা:** প্রিন্টকৃত ফরম, পেমেন্ট স্লিপ এবং প্রয়োজনীয় ছবি ও ডকুমেন্টস নিজ কলেজের সংশ্লিষ্ট বিভাগে নির্ধারিত শেষ তারিখের পূর্বে জমা দিন।
7. **কলেজ ভেরিফিকেশন:** কলেজ কর্তৃপক্ষ অনলাইন প্যানেলে আপনার পেমেন্ট ও ফরম ভেরিফাই করবে। কলেজ কনফার্মেশনের পরই আপনার এডমিট কার্ড ইস্যু হবে।

#### ৩. পাসওয়ার্ড বা একাউন্ট সংক্রান্ত সমস্যার সমাধান:
• **পাসওয়ার্ড ভুলে গেলে:** লগইন পেজের নিচে **'Forgot Password'** অপশনে ক্লিক করে রেজিস্ট্রেশন নম্বর ও নিবন্ধিত মোবাইল নম্বরে ওটিপি দিয়ে রিসেট করুন।
• **তথ্য অমিল বা ডাটা নট ফাউন্ড:** যদি বিষয় কোড না আসে বা ডাটা লক দেখায়, অনতিবিলম্বে নিজ কলেজের আইসিটি সেল অথবা পরীক্ষা শাখায় যোগাযোগ করুন।
• **সাপোর্ট সার্ভিস:** সমাধানের জন্য আমাদের চ্যাটবট ড্যাশবোর্ডের **টোকেন সার্ভিস (Token Service)**-এ আইসিটি সাপোর্ট ডেস্ক বরাবর একটি অভিযোগ টোকেন খুলতে পারেন।"""


# 7. Services Mega-Menu Breakdown Replies
SERVICES_MENU_REPLY = """### 🏛️ জাতীয় বিশ্ববিদ্যালয় সকল অনলাইন সেবা পোর্টাল তালিকা (Services Menu)

জাতীয় বিশ্ববিদ্যালয়ের অফিসিয়াল ওয়েবসাইট ([nu.ac.bd](https://www.nu.ac.bd/)) অনুযায়ী মূল সেবাসমূহ নিচে দেওয়া হলো:

#### 👥 স্টুডেন্ট ও পরীক্ষা সংক্রান্ত সেবা:
1. 📜 **[স্টুডেন্ট অনলাইন সার্ভিস পোর্টাল (nu-app)](http://103.113.200.68/nu-app/)**: সার্টিফিকেট, মার্কশিট, ট্রান্সক্রিপ্ট, রেজিস্ট্রেশন কার্ড ও টিসি আবেদন।
2. 🔄 **[খাতা পুনর্মূল্যায়ন ও পুনঃনিরীক্ষণ (Re-Evaluation)](https://results.nu.ac.bd/)**: ফলাফল প্রকাশের ৩০ দিনের মধ্যে সোনালী সেবায় আবেদন।
3. 🔍 **[সনদপত্র ও WES ভেরিফিকেশন (Verification Service)](http://103.113.200.68/nu-app/)**: দেশি ও বিদেশি উচ্চশিক্ষার ডকুমেন্ট সত্যায়ন।
4. 🪪 **সংশোধিত ও ডুপ্লিকেট এডমিট কার্ড**: ভুল প্রবেশপত্র সংশোধন ও উত্তোলনের আবেদন।
5. 🏢 **ওয়ান স্টপ সার্ভিস সেন্টার (One Stop Services)**: গাজীপুর ও আঞ্চলিক কেন্দ্র থেকে সরাসরি জরুরি সনদ বিতরণ।

#### 🎓 কলেজ ও প্রতিষ্ঠান সংক্রান্ত সেবা:
1. 🏫 **কলেজ লগইন (College Login)**: টিসি অনুমোদন (e-TC NOC), গভর্নিং বডি ও অ্যাডহক কমিটি, অধিভুক্তি নবায়ন ও শিক্ষক নিয়োগ।
2. 📊 **[সিএমইএস (CMES - College Monitoring & Evaluation)](https://www.nu.ac.bd/)**: কলেজ তদারকি ও একাডেমিক মান নিশ্চিতকরণ।
3. 🗺️ **কলেজ প্রোফাইল ও কলেজ ম্যাপ**: দেশের সকল অধিভুক্ত কলেজের বিস্তারিত তথ্য ও অবস্থান।

#### 👨‍🏫 শিক্ষক ও কর্মকর্তা সেবা:
1. 💻 **[টিএমআইএস (TMIS - Teachers Management Information System)](http://tmis.nu.ac.bd/)**: শিক্ষকদের কেন্দ্রীয় ডাটাবেজ।
2. 📚 **[টিটিআইএস (TTIS - Teachers Training Information System)](http://ttis.nu.ac.bd/)**: শিক্ষক প্রশিক্ষণ ও ওয়ার্কশপ পোর্টাল।
3. 📝 **[মৌখিক ও ব্যবহারিক পরীক্ষার বিল (Viva/Practical Bill)](http://ems.nu.ac.bd/)**: পরীক্ষকদের অনলাইন বিল এন্ট্রি।
4. 📧 **[ওয়েবমেইল (Webmail)](https://mail.nu.ac.bd/)** ও **কর্মচারী সেবা (Employee Services)**।

#### 🌐 অন্যান্য গুরুত্বপূর্ণ পোর্টাল:
• 💳 **সোনালী সেবা (Sonali Seba e-Payment)** • 💼 **চাকরি পোর্টাল (Job Portal)** • 🎥 **[অনলাইন ভিডিও লেকচার গ্যালারি](https://www.nu.ac.bd/)**
"""

CMES_REPLY = """### 📊 কলেজ মনিটরিং অ্যান্ড ইভ্যালুয়েশন সিস্টেম (CMES)

**CMES (College Monitoring and Evaluation System)** হলো জাতীয় বিশ্ববিদ্যালয়ের আওতাধীন সকল কলেজের একাডেমিক ও প্রশাসনিক কার্যক্রম তদারকির ডিজিটাল পোর্টাল:

• **উদ্দেশ্য:** কলেজের পাঠদান মান, শিক্ষক ও শিক্ষার্থী উপস্থিতি এবং ল্যাব/অবকাঠামোগত উন্নয়ন পর্যবেক্ষণ।
• **ব্যবহারকারী:** জাতীয় বিশ্ববিদ্যালয় কলেজ পরিদর্শন শাখা ও কলেজ প্রশাসন।
👉 **বিস্তারিত দেখুন:** [জাতীয় বিশ্ববিদ্যালয় পোর্টাল](https://www.nu.ac.bd/)"""

WES_VERIFICATION_REPLY = """### 🔍 সনদপত্র, নম্বরপত্র ও WES ভেরিফিকেশন নির্দেশিকা (Verification Service)

বিদেশি উচ্চশিক্ষা বা আন্তর্জাতিক স্বীকৃতির জন্য জাতীয় বিশ্ববিদ্যালয় থেকে সার্টিফিকেট ও ট্রান্সক্রিপ্ট সত্যায়ন (WES / ECE / ICAS):

1. **অনলাইন আবেদন:** [জাতীয় বিশ্ববিদ্যালয় স্টুডেন্ট পোর্টাল (http://103.113.200.68/nu-app/)](http://103.113.200.68/nu-app/) এ Student Login করে **'Verification / WES'** অপশনে যান।
2. **ডকুমেন্ট আপলোড:** আপনার সকল বর্ষের একাডেমিক সার্টিফিকেট, মার্কশিট এবং WES Reference Number ফরম আপলোড করুন।
3. **ফি প্রদান:** নির্ধারিত ফি সোনালী সেবার মাধ্যমে পরিশোধ করুন।
4. **সরাসরি প্রেরণ:** বিশ্ববিদ্যালয় পরীক্ষা নিয়ন্ত্রক দপ্তর সরাসরি সিলগালা খামে বা ইলেকট্রনিক মাধ্যমে WES-এ প্রেরণ করে।
"""

# 6. Preloaded Certificate, Transcript & TC Services
TC_REPLY = """### 🏛️ জাতীয় বিশ্ববিদ্যালয় কলেজ ছাড়পত্র (TC / e-TC) নেওয়ার সম্পূর্ণ নিয়মাবলী

জাতীয় বিশ্ববিদ্যালয়ের নিয়মিত শিক্ষার্থীদের এক কলেজ থেকে অন্য কলেজে স্থানান্তরের (e-TC) আবেদন প্রক্রিয়া সম্পূর্ণ অনলাইনে সম্পন্ন করতে হয়:

#### ১. আবেদন যোগ্যতা ও প্রযোজ্য শর্তাবলী:
• **কোর্স ও বর্ষ:** সাধারণত অনার্স বা ডিগ্রি কোর্সের ১ম বর্ষ উত্তীর্ণ হয়ে ২য় বর্ষে অথবা ২য় বর্ষ উত্তীর্ণ হয়ে ৩য় বর্ষে ভর্তির পর ছাড়পত্রের আবেদন করা যায়। পরীক্ষার ফরম পূরণ চলাকালীন সময়ে টিসি আবেদন স্থগিত থাকে।
• **উপযুক্ত কারণ:** অভিভাবকের চাকুরিজাত স্থানান্তর, স্থায়ী ঠিকানা পরিবর্তন, দূরবর্তী দূরত্ব বা শারীরিক প্রতিবন্ধকতা ইত্যাদি যুক্তিসঙ্গত কারণ উল্লেখ করতে হয়। একই জেলায় সাধারণত সরকারি থেকে সরকারি বা বেসরকারি থেকে বেসরকারি কলেজে স্থানান্তর হওয়া যায়।

#### ২. অনলাইন আবেদনের সঠিক ধাপসমূহ:
1. **স্টুডেন্ট লগইন:** জাতীয় বিশ্ববিদ্যালয়ের অফিসিয়াল [স্টুডেন্ট সার্ভিসেস পোর্টাল (http://103.113.200.68/nu-app/)](http://103.113.200.68/nu-app/) ভিজিট করুন।
2. **রেজিস্ট্রেশন:** পূর্বে একাউন্ট না থাকলে 'Student Registration' অপশনে গিয়ে আপনার রোল, রেজিস্ট্রেশন নম্বর ও শিক্ষাবর্ষ দিয়ে সাইন-আপ করুন।
3. **টিসি ফরম পূরণ:** ড্যাশবোর্ডে লগইন করে **'Academic Services' -> 'College Transfer (e-TC)'** নির্বাচন করুন।
4. **কাঙ্ক্ষিত কলেজ নির্বাচন:** ড্রপডাউন মেনু থেকে আপনার পছন্দকৃত গন্তব্য কলেজ (Target College) ও বিভাগ/বিষয় নির্বাচন করুন এবং স্থানান্তরের কারণ লিখে প্রয়োজনীয় সনদ/প্রত্যয়নপত্র আপলোড করুন।
5. **আবেদন সাবমিট ও পে-স্লিপ প্রিন্ট:** সাবমিট করার পর সোনালী সেবার অনলাইন ফি পে-স্লিপ স্বয়ংক্রিয়ভাবে তৈরি হবে।

#### ৩. ফি ও পরিশোধ পদ্ধতি:
• **নির্ধারিত ফি:** জাতীয় বিশ্ববিদ্যালয় নির্ধারিত টিসি ফি ১,০০০/- (এক হাজার) টাকা।
• **পেমেন্ট:** সোনালী সেবা পে-স্লিপটি প্রিন্ট করে যেকোনো সোনালী ব্যাংক শাখায় জমা দিন অথবা অনলাইন সোনালী পেমেন্ট গেটওয়ের মাধ্যমে (বিকাশ/নগদ/রকেট/কার্ড) পরিশোধ করুন।

#### ৪. ছাড়পত্র অনুমোদন ও ভর্তি সম্পন্নকরণ:
1. **বর্তমান কলেজের এনওসি (NOC):** ফি জমা দেওয়ার পর আবেদনটি বর্তমান কলেজের অধ্যক্ষের অনলাইন প্যানেলে যায় এবং অধ্যক্ষ অনুমোদন প্রদান করেন।
2. **গন্তব্য কলেজের এনওসি (NOC):** এরপর প্রস্তাবিত নতুন কলেজের অধ্যক্ষ আসন শূন্য থাকা সাপেক্ষে অনলাইন অনাপত্তি (Acceptance) দেন।
3. **বিশ্ববিদ্যালয় চূড়ান্ত অনুমোদন:** উভয় কলেজ এনওসি দেওয়ার পর জাতীয় বিশ্ববিদ্যালয়ের রেজিস্ট্রেশন শাখা যাচাই করে চূড়ান্ত ছাড়পত্র ইস্যু করে।
4. **চূড়ান্ত ছাড়পত্র ডাউনলোড:** অনুমোদনের এসএমএস পাওয়ার পর স্টুডেন্ট পোর্টাল থেকে অনুমোদিত **e-TC Order Copy** ডাউনলোড করে নতুন কলেজে সরাসরি ভর্তি সম্পন্ন করুন।

🔗 **জরুরি অফিসিয়াল লিংক:**
- **স্টুডেন্ট ERP লগইন ও আবেদন:** [http://103.113.200.68/nu-app/](http://103.113.200.68/nu-app/)
- **নোটিশ বোর্ড:** [সকল নোটিশ (nu.ac.bd)](https://www.nu.ac.bd/recent-news-notice.php)"""

CERTIFICATE_REPLY = """### 📜 জাতীয় বিশ্ববিদ্যালয় সার্টিফিকেট উত্তোলন — ফি ও উত্তোলনের পূর্ণাঙ্গ নিয়মাবলী

জাতীয় বিশ্ববিদ্যালয়ের সকল মূল সনদ, সাময়িক সনদ, নম্বরপত্র (মার্কশিট) এবং একাডেমিক ট্রান্সক্রিপ্ট উত্তোলনের আবেদন সম্পূর্ণ অনলাইন পোর্টালের মাধ্যমে করতে হয়:

#### ১. অনলাইন আবেদনের পোর্টাল ও প্রক্রিয়া:
1. **পোর্টাল লিংক:** জাতীয় বিশ্ববিদ্যালয় স্টুডেন্ট সার্ভিসেস পোর্টাল: [http://103.113.200.68/nu-app/](http://103.113.200.68/nu-app/)
2. **লগইন ও সার্ভিস নির্বাচন:** রেজিস্ট্রেশন ও মোবাইল নম্বর দিয়ে লগইন করে **'Certificate Application' / 'Document Services'** সেকশনে প্রবেশ করুন।
3. **কাঙ্ক্ষিত সনদ নির্বাচন:** ড্রপডাউন থেকে মূল সনদ (Original), সাময়িক সনদ (Provisional), মার্কশিট (Marksheet) বা ট্রান্সক্রিপ্ট (Transcript) নির্বাচন করুন।
4. **ডকুমেন্ট আপলোড:** সকল বর্ষের প্রবেশপত্র (Admit Card), নম্বরপত্র ও রেজিস্ট্রেশন কার্ডের স্পষ্ট স্ক্যান কপি যুক্ত করুন।

#### ২. অফিসিয়াল ফি তালিকা (সোনালী সেবা):
• **মূল সনদপত্র (Original Certificate):**
  - সাধারণ ডেলিভারি (Regular): **৫০০/- টাকা**
  - জরুরি ডেলিভারি (Urgent): **১,০০০/- টাকা**
• **সাময়িক সনদপত্র (Provisional Certificate):**
  - সাধারণ ডেলিভারি: **৩০০/- টাকা**
  - জরুরি ডেলিভারি: **৫০০/- টাকা**
• **একাডেমিক ট্রান্সক্রিপ্ট (Official Transcript):**
  - প্রতি কপি সাধারণ: **৭০০/- টাকা**
  - জরুরি ডেলিভারি: **১,০০০/- টাকা**
• **নম্বরপত্র / গ্রেডশিট (Marksheet):**
  - প্রতি বর্ষের মার্কশিট: **৩০০/- টাকা** (জরুরি ৫০০/- টাকা)
*(ব্যাংক চার্জ ও সোনালী সেবা ট্রানজেকশন ফি প্রযোজ্য হতে পারে)*

#### ৩. ফি পরিশোধ ও ডকুমেন্ট গ্রহণ:
• **ফি প্রদান:** সোনালী সেবা ই-পেমেন্ট গেটওয়ের মাধ্যমে সরাসরি কার্ড/বিকাশ/নগদে অথবা সোনালী ব্যাংকের যেকোনো শাখায় পে-স্লিপ জমা দেওয়া যায়।
• **ডেলিভারি মাধ্যম:**
  - **ওয়ান স্টপ সার্ভিস (One Stop Service):** জরুরি আবেদনের ক্ষেত্রে গাজীপুর মূল ক্যাম্পাসের ওয়ান স্টপ সার্ভিস কাউন্টার থেকে নির্ধারিত তারিখে মূল রশিদ ও আইডি কার্ড দেখিয়ে সরাসরি সনদ গ্রহণ করা যায়।
  - **আঞ্চলিক কেন্দ্র বা ডাকযোগে:** সাধারণ আবেদনের ক্ষেত্রে সংশ্লিষ্ট আঞ্চলিক কেন্দ্র অথবা নিজ কলেজের ঠিকানায় সনদ পৌঁছে দেওয়া হয়।

🔗 **অফিসিয়াল পোর্টাল লিংক:** [http://103.113.200.68/nu-app/](http://103.113.200.68/nu-app/)"""


CORRECTION_REPLY = """### ✏️ সনদপত্র, নম্বরপত্র ও তথ্যের ভুল সংশোধন নির্দেশিকা (Document Corrections)

নাম, পিতা-মাতার নাম, রোল, রেজিস্ট্রেশন নম্বর বা ফলাফলের ভুল সংশোধনের আবেদন প্রক্রিয়া:

1. **অনলাইন আবেদন (ERP Portal):**
   - [জাতীয় বিশ্ববিদ্যালয় ERP সার্ভিসেস পোর্টাল (http://103.113.200.68/nu-app/)](http://103.113.200.68/nu-app/) এ Student Login করে **'Document Correction'** অপশন বেছে নিন।
2. **প্রয়োজনীয় কাগজপত্র:**
   - এসএসসি/এইচএসসি মূল সনদ ও নম্বরপত্রের সত্যায়িত কপি, জাতীয় পরিচয়পত্র/জন্মনিবন্ধন, এবং কলেজ প্রত্যয়নপত্র আপলোড করুন।
3. **ফি ও সোনালী সেবা:**
   - সংশোধনের জন্য নির্ধারিত ফি সোনালী সেবার মাধ্যমে পরিশোধ করতে হবে।
4. **যাচাই ও সংশোধিত কপি:**
   - একাডেমিক কাউন্সিল ও সংশ্লিষ্ট পরীক্ষা শাখা যাচাই শেষে সংশোধিত ডকুমেন্ট অনুমোদন করে।

🔗 **সংশোধন পোর্টাল লিংক:** [http://103.113.200.68/nu-app/](http://103.113.200.68/nu-app/)"""

ERP_SERVICES_REPLY = """### 🌐 জাতীয় বিশ্ববিদ্যালয় স্টুডেন্ট ERP সার্ভিসেস ও অনলাইন সেবা পোর্টাল

জাতীয় বিশ্ববিদ্যালয়ের শিক্ষার্থীদের সকল একাডেমিক ও প্রশাসনিক সেবা প্রদানের জন্য কেন্দ্রীয় **Student ERP Services Portal** কার্যকর রয়েছে:

**প্রধান অনলাইন সেবাসমূহ:**
• 📜 **কলেজ ট্রান্সফার / টিসি (College Transfer / e-TC)**
• 🎓 **মূল ও সাময়িক সনদপত্র আবেদন (Original & Provisional Certificate)**
• 📊 **একাডেমিক ট্রান্সক্রিপ্ট ও নম্বরপত্র (Academic Transcript & Marksheet)**
• ✏️ **নাম ও তথ্যের ভুল সংশোধন (Document / Name Correction)**
• 📋 **দ্বৈত সনদ ও মাইগ্রেশন সার্টিফিকেট (Duplicate Certificate & Migration)**
• 💳 **সোনালী সেবা পে-স্লিপ ও অনলাইন ফি ট্র্যাকিং**

👉 **স্টুডেন্ট ERP লগইন লিংক:** [http://103.113.200.68/nu-app/](http://103.113.200.68/nu-app/) অথবা [http://103.113.200.68/nu-app/](http://103.113.200.68/nu-app/)"""



HELPDESK_REPLY = """### 📞 জাতীয় বিশ্ববিদ্যালয় হেল্পডেস্ক ও জরুরি যোগাযোগ নম্বর

জাতীয় বিশ্ববিদ্যালয়ের অফিসিয়াল যোগাযোগের জরুরি নম্বরসমূহ (সব নম্বর ইংরেজি সংখ্যায় 0-9 ব্যবহার করা হয়েছে):

• **সেন্ট্রাল পিএবিএক্স (PABX):** +88029291017, +88029291018
• **পরীক্ষা নিয়ন্ত্রক দপ্তর:** 02-9291019, 02-9291020
• **ভর্তি ও রেজিস্ট্রেশন সেল:** 02-9291038
• **আইসিটি ও ইআরপি সাপোর্ট শাখা:** 02-9291035, 02-9291036
• **ইমেইল:** info@nu.ac.bd, registrar@nu.ac.bd
• **অনলাইন সার্ভিস সাপোর্ট:** http://103.113.200.68/nu-app/

📌 *যেকোনো জরুরি বিষয়ে সরাসরি আমাদের সাপোর্ট সেন্টারে টোকেন খুলতে পারেন।*"""

# Direct normalized phrase mapping for instant lookups (< 0.001s)
INSTANT_LOOKUP_MAP: Dict[str, ChatResponse] = {}

def _init_instant_lookups():
    # Helpdesk & Contacts
    helpdesk_triggers = [
        "helpdesk", "contact", "phone", "phone number", "contact number", "hotline",
        "হেল্পডেস্ক", "যোগাযোগ", "ফোন নম্বর", "মোবাইল নম্বর", "হেল্পলাইন", "যোগাযোগের ফোন নম্বর",
        "হেল্পডেস্ক বা যোগাযোগের ফোন নম্বর দিন", "যোগাযোগের নম্বর"
    ]
    for trig in helpdesk_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=HELPDESK_REPLY,
            citations=CITATIONS_GENERAL,
            intent="HELPDESK_CONTACT",
            skill_used="nu_general",
            suggested_chips=["🎫 সাপোর্ট টোকেন খুলুন", "🌐 স্টুডেন্ট পোর্টাল", "📄 নোটিশ বোর্ড", "🏠 মূল মেনু"]
        )

    # Greetings & Salutations
    greeting_triggers = [
        "hi", "hello", "hey", "start", "menu", "help", "hlo", "helo", "hy",
        "হাই", "হ্যালো", "শুরু", "মেনু", "সাহায্য", "আসসালামু আলাইকুম", "সালাম",
        "assalamu alaikum", "assalamualaikum", "kemon acho", "kemon achen",
        "কেমন আছেন", "কে আছো", "জাতীয় বিশ্ববিদ্যালয়", "জাতীয় বিশ্ববিদ্যালয়",
        "nu", "national university", "info"
    ]
    for trig in greeting_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=WELCOME_REPLY,
            citations=CITATIONS_GENERAL,
            intent="GREETING",
            skill_used="nu_general",
            suggested_chips=["🎫 টোকেন সার্ভিস (Token Service)", "📑 টোকেন স্ট্যাটাস চেক", "📄 সাম্প্রতিক নোটিশ", "🎓 ভর্তি তথ্য"]
        )

    # Admissions
    admission_triggers = [
        "admission", "admissions", "apply", "how to apply", "admission procedure",
        "ভর্তি", "ভর্তি তথ্য", "ভর্তি প্রক্রিয়া", "অনার্স ভর্তি", "ডিগ্রি ভর্তি", "মাস্টার্স ভর্তি", "ভর্তি পোর্টাল"
    ]
    for trig in admission_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=ADMISSION_REPLY,
            citations=CITATIONS_ADMISSION,
            intent="ADMISSION_INFO",
            skill_used="admission",
            suggested_chips=["🎓 অনার্স ১ম বর্ষ ভর্তি", "📄 ভর্তি সার্কুলার", "🎫 ভর্তি সহায়তা টোকেন", "🏠 মূল মেনু"]
        )

    # Exam & Routines
    exam_triggers = [
        "exam", "examination", "routine", "exam routine", "admit card",
        "পরীক্ষা", "পরীক্ষার রুটিন", "রুটিন", "এডমিট কার্ড", "প্রবেশপত্র", "পরীক্ষার সময়সূচি"
    ]
    for trig in exam_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=EXAM_REPLY,
            citations=CITATIONS_EMS,
            intent="EXAM_ROUTINE",
            skill_used="examination",
            suggested_chips=["📝 পরীক্ষার রুটিন দেখুন", "🎫 পরীক্ষার টোকেন খুলুন", "📊 ফলাফল চেক", "🏠 মূল মেনু"]
        )

    # Results & CGPA
    result_triggers = [
        "result", "results", "cgpa", "gpa", "marksheet", "rescrutiny",
        "ফলাফল", "রেজাল্ট", "সিজিপিএ", "মার্কশিট", "পুনর্নিরীক্ষণ", "বোর্ড চ্যালেঞ্জ"
    ]
    for trig in result_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=RESULTS_REPLY,
            citations=CITATIONS_RESULTS,
            intent="RESULT_INFO",
            skill_used="result",
            suggested_chips=["📊 ফলাফল পোর্টাল লিংক", "📱 SMS রেজাল্ট নিয়ম", "🎫 ফলাফল সংক্রান্ত টোকেন", "🏠 মূল মেনু"]
        )

    # Form Fill-Up & EMS
    ems_triggers = [
        "form fillup", "form fill up", "ems", "ems login", "password reset", "student portal",
        "ফরম পূরণ", "ইএমএস", "ইএমএস লগইন", "পাসওয়ার্ড ভুলে গেছি", "ফরম ফিলাপ",
        "ডিগ্রি ও অনার্স ফরম পূরণের নিয়মাবলি", "ফরম পূরণ (ems)", "ফরম পূরণ করার নিয়ম",
        "ইএমএস স্টুডেন্ট লগইন", "ems student login", "https://ems.nu.ac.bd/student-login",
        "ems.nu.ac.bd/student-login", "ফরম পূরণের নিয়ম", "ফরম পূরণ (ems)"
    ]
    for trig in ems_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=EMS_REPLY,
            citations=CITATIONS_EMS,
            intent="EMS_INFO",
            skill_used="service_credentials",
            suggested_chips=["💻 EMS লগইন পোর্টাল", "🔐 ইএমএস পাসওয়ার্ড রিসেট", "🎫 ফরম পূরণ সাপোর্ট টোকেন", "🏠 মূল মেনু"]
        )


    # Services Mega Menu & Specialized Modules
    menu_triggers = [
        "services", "service menu", "all services", "সেবা", "সার্ভিস মেনু", "সকল সেবা", "সার্ভিস"
    ]
    for trig in menu_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=SERVICES_MENU_REPLY,
            citations=CITATIONS_GENERAL,
            intent="SERVICES_MENU_INFO",
            skill_used="nu_general",
            suggested_chips=["📜 স্টুডেন্ট nu-app পোর্টাল", "🔍 WES ভেরিফিকেশন", "📊 CMES কলেজ মনিটরিং", "🏠 মূল মেনু"]
        )

    cmes_triggers = ["cmes", "college monitoring", "কলেজ মনিটরিং", "সিএমইএস"]
    for trig in cmes_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=CMES_REPLY,
            citations=CITATIONS_GENERAL,
            intent="CMES_INFO",
            skill_used="nu_general",
            suggested_chips=["📊 CMES পোর্টাল", "🏛️ কলেজ পরিদর্শন দপ্তর", "🏠 মূল মেনু"]
        )

    wes_triggers = ["wes", "wes verification", "verification service", "ডকুমেন্ট ভেরিফিকেশন", "সত্যায়ন", "ইসিএ"]
    for trig in wes_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=WES_VERIFICATION_REPLY,
            citations=CITATIONS_ERP_SERVICES,
            intent="WES_VERIFICATION_INFO",
            skill_used="service_credentials",
            suggested_chips=["🔍 WES আবেদন লিংক", "💳 সোনালী সেবা ফি", "🎫 ভেরিফিকেশন টোকেন", "🏠 মূল মেনু"]
        )

    # College Transfer / TC (ছাড়পত্র)
    tc_triggers = [
        "tc", "transfer certificate", "college transfer", "tc form", "tc application",
        "টিসি", "ছাড়পত্র", "কলেজ পরিবর্তন", "কলেজ ট্রান্সফার", "টিসি ফরম", "টিসি আবেদন", "ছাড়পত্র",
        "কলেজ ছাড়পত্র (tc) নেওয়ার উপায় কি?", "কলেজ ছাড়পত্র (tc) নেওয়ার উপায় কি", "কলেজ ছাড়পত্র নেওয়ার নিয়ম",
        "টিসি নেওয়ার নিয়ম", "কলেজ পরিবর্তন করার নিয়ম", "কলেজ ছাড়পত্র", "কলেজ ছাড়পত্র (tc)", "e-tc", "etc",
        "ছাড়পত্র নেওয়ার উপায়", "ছাড়পত্র নেওয়ার উপায়"
    ]
    for trig in tc_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=TC_REPLY,
            citations=CITATIONS_ERP_SERVICES,
            intent="TC_INFO",
            skill_used="service_credentials",
            suggested_chips=["📜 স্টুডেন্ট ERP পোর্টাল লিংক", "💳 সোনালী সেবা ফি", "🎫 টিসি সহায়তা টোকেন", "🏠 মূল মেনু"]
        )

    # Document Corrections (ভুল সংশোধন)
    correction_triggers = [
        "correction", "name correction", "marksheet correction", "certificate correction", "spelling mistake",
        "সংশোধন", "নাম সংশোধন", "ভুল সংশোধন", "মার্কশিট সংশোধন", "সনদপত্র সংশোধন", "তথ্য সংশোধন"
    ]
    for trig in correction_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=CORRECTION_REPLY,
            citations=CITATIONS_ERP_SERVICES,
            intent="CORRECTION_INFO",
            skill_used="service_credentials",
            suggested_chips=["✏️ ERP সংশোধন পোর্টাল", "💳 সোনালী সেবা পে-স্লিপ", "🎫 সংশোধন সাপোর্ট টোকেন", "🏠 মূল মেনু"]
        )

    # Student ERP Services Portal
    erp_triggers = [
        "erp", "student login", "erp services", "103.113.200.68/nu-app", "103.113.200.68/nu-app", "nu-app", "nu app", "103.113.200.68", "student portal",
        "ইআরপি", "স্টুডেন্ট লগইন", "অনলাইন সার্ভিস", "ইআরপি সার্ভিস", "ছাত্র পোর্টাল"
    ]
    for trig in erp_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=ERP_SERVICES_REPLY,
            citations=CITATIONS_ERP_SERVICES,
            intent="ERP_SERVICES_INFO",
            skill_used="service_credentials",
            suggested_chips=["🌐 ERP লগইন পোর্টাল", "📜 টিসি (TC) আবেদন", "🎓 সার্টিফিকেট আবেদন", "🏠 মূল মেনু"]
        )

    # Certificates & Marksheets
    cert_triggers = [
        "certificate", "transcript", "original certificate", "provisional certificate",
        "সার্টিফিকেট", "নম্বরপত্র", "ট্রান্সক্রিপ্ট", "মূল সনদ", "সাময়িক সনদ",
        "সার্টিফিকেট উত্তোলন", "অনলাইনে মূল সার্টিফিকেট উত্তোলনের নিয়ম ও ফি কত?", "অনলাইনে মূল সার্টিফিকেট উত্তোলনের নিয়ম ও ফি কত",
        "ফি ও উত্তোলনের নিয়ম", "সনদ উত্তোলনের নিয়ম", "সার্টিফিকেট ফি", "সনদ উত্তোলন", "মার্কশিট উত্তোলন", "ট্রান্সক্রিপ্ট উত্তোলন",
        "সার্টিফিকেট ফি কত", "মূল সার্টিফিকেট উত্তোলন"
    ]
    for trig in cert_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=CERTIFICATE_REPLY,
            citations=CITATIONS_GENERAL,
            intent="CERTIFICATE_INFO",
            skill_used="document_search",
            suggested_chips=["📜 সার্টিফিকেট আবেদনের নিয়ম", "🎫 সার্টিফিকেট সহায়তা টোকেন", "🏠 মূল মেনু"]
        )

    # Main Menu & Home Triggers
    main_menu_triggers = [
        "মূল মেনু", "মেইন মেনু", "main menu", "menu", "মেনু", "home", "হোম", "🏠 মূল মেনু", "মূল মেনুতে ফিরুন",
        "প্রধান মেনু", "মূলমেনু", "mainmenu"
    ]
    for trig in main_menu_triggers:
        INSTANT_LOOKUP_MAP[trig] = ChatResponse(
            reply=MAIN_MENU_REPLY,
            citations=CITATIONS_GENERAL,
            intent="MAIN_MENU_INFO",
            skill_used="nu_general",
            suggested_chips=["📘 অনার্স পরীক্ষা", "📗 ডিগ্রি পরীক্ষা", "📙 মাস্টার্স পরীক্ষা", "🎓 প্রফেশনাল পরীক্ষা"]
        )

_init_instant_lookups()

def get_preloaded_response(query: str) -> Optional[ChatResponse]:
    """
    Checks if a normalized query has a preloaded instant response (< 0.001s execution).
    """
    if TOKEN_ID_REGEX.search(query):
        return None

    normalized = query.lower().strip(" \t\n\r.?!,;:-_~`@#$%^&*()+=/\\|")
    if normalized in INSTANT_LOOKUP_MAP:
        return INSTANT_LOOKUP_MAP[normalized]

    # 1. Instant check for main menu variations
    if any(k in normalized for k in ["মূল মেনু", "মেইন মেনু", "main menu", "মূলমেনু", "mainmenu", "🏠 মূল মেনু"]):
        return INSTANT_LOOKUP_MAP.get("মূল মেনু")
    if normalized in ["menu", "মেনু", "home", "হোম"]:
        return INSTANT_LOOKUP_MAP.get("মূল মেনু")

    # 2. Check TC (ছাড়পত্র / Transfer Certificate) key phrases
    if any(k in normalized for k in ["ছাড়পত্র", "ছাড়পত্র", "টিসি", "কলেজ পরিবর্তন", "কলেজ ট্রান্সফার", "tc", "transfer certificate", "e-tc"]):
        return INSTANT_LOOKUP_MAP.get("tc")

    # 3. Check Certificate (সার্টিফিকেট / নম্বরপত্র / উত্তোলন / সনদ) key phrases
    if any(k in normalized for k in ["সার্টিফিকেট", "সাময়িক সনদ", "সাময়িক সনদ", "মূল সনদ", "ট্রান্সক্রিপ্ট", "উত্তোলন", "certificate", "transcript", "নম্বরপত্র"]):
        return INSTANT_LOOKUP_MAP.get("certificate")

    # 4. Check EMS / Form Fill-Up key phrases
    if any(k in normalized for k in ["ফরম পূরণ", "ফরম পুরণ", "ইএমএস", "ems", "form fill", "student-login"]):
        return INSTANT_LOOKUP_MAP.get("ems")

    # 5. Check key intent phrases
    if any(k in normalized for k in ["যোগাযোগের ফোন নম্বর", "ফোন নম্বর", "হেল্পডেস্ক", "contact number", "phone number"]):
        return INSTANT_LOOKUP_MAP.get("helpdesk")
    
    # 6. Check word-level match for short 1-2 word queries
    words = normalized.split()
    if len(words) <= 2:
        for w in words:
            if w in INSTANT_LOOKUP_MAP:
                return INSTANT_LOOKUP_MAP[w]
                
    return None


