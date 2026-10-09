import json
import os
from datetime import datetime, date, timedelta
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle

GREEN = (0.09, 0.42, 0.34, 1)
PALE = (0.91, 0.96, 0.93, 1)
BG = (0.96, 0.975, 0.965, 1)
INK = (0.09, 0.16, 0.13, 1)
MUTED = (0.40, 0.47, 0.43, 1)
RED = (0.72, 0.20, 0.25, 1)

def fmt_money(value):
    try:
        return f"{value:,.2f}".rstrip("0").rstrip(".") + " دج"
    except Exception:
        return str(value) + " دج"

def parse_dt(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return datetime.now()

class Card(BoxLayout):
    def __init__(self, bg=(1,1,1,1), radius=16, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(14)
        self.spacing = dp(9)
        with self.canvas.before:
            Color(*bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._update_rect, size=self._update_rect)
    def _update_rect(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

class PurchaseRow(BoxLayout):
    def __init__(self, purchase, on_delete, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(76),
                         padding=[dp(10), dp(7)], spacing=dp(8), **kwargs)
        with self.canvas.before:
            Color(1,1,1,1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(13)])
        self.bind(pos=self._rect, size=self._rect)
        icon = Label(text="🛍", size_hint_x=None, width=dp(42), font_size="22sp", color=GREEN)
        self.add_widget(icon)
        mid = BoxLayout(orientation="vertical", spacing=dp(2))
        name = Label(text=purchase.get("name",""), color=INK, bold=True, font_size="14sp",
                     halign="right", valign="middle", text_size=(None,None))
        stamp = parse_dt(purchase.get("date","")).strftime("%Y-%m-%d  %H:%M")
        meta = Label(text=f"الكمية: {purchase.get('qty',1)} · {stamp}", color=MUTED,
                     font_size="10sp", halign="right")
        mid.add_widget(name); mid.add_widget(meta)
        self.add_widget(mid)
        side = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(94), spacing=dp(3))
        price = Label(text=fmt_money(float(purchase.get("price",0))*int(purchase.get("qty",1))),
                      color=INK, bold=True, font_size="12sp")
        delete = Button(text="حذف", size_hint_y=None, height=dp(29), background_normal="",
                        background_color=(1,.93,.93,1), color=RED, font_size="11sp")
        delete.bind(on_release=lambda *_: on_delete(purchase.get("id")))
        side.add_widget(price); side.add_widget(delete)
        self.add_widget(side)
    def _rect(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size

class MoshtarayatiApp(App):
    title = "مشترياتي"

    def build(self):
        Window.clearcolor = BG
        self.period = "day"
        self.selected_date = date.today()
        self.purchases = []
        self.load_data()

        root = BoxLayout(orientation="vertical", padding=[dp(14),dp(12),dp(14),dp(10)], spacing=dp(10))
        header = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(10))
        logo = Label(text="🛍", size_hint_x=None, width=dp(48), font_size="27sp",
                     color=(1,1,1,1))
        with logo.canvas.before:
            Color(*GREEN); logo_bg = RoundedRectangle(pos=logo.pos, size=logo.size, radius=[dp(14)])
        logo.bind(pos=lambda w,v: setattr(logo_bg,'pos',v), size=lambda w,v: setattr(logo_bg,'size',v))
        header.add_widget(logo)
        titlebox = BoxLayout(orientation="vertical", spacing=0)
        titlebox.add_widget(Label(text="مشترياتي", color=INK, bold=True, font_size="23sp",
                                  halign="right", valign="middle"))
        titlebox.add_widget(Label(text="تابع مصروفك، خطوة بخطوة", color=MUTED, font_size="12sp",
                                  halign="right", valign="middle"))
        header.add_widget(titlebox)
        root.add_widget(header)

        self.hero = Card(orientation="vertical", size_hint_y=None, height=dp(126), bg=GREEN, radius=20)
        self.hero.add_widget(Label(text="إجمالي مشتريات اليوم", color=(.88,1,.94,1), font_size="13sp",
                                  halign="right", size_hint_y=None, height=dp(22)))
        self.hero_amount = Label(text="0 دج", color=(1,1,1,1), bold=True, font_size="30sp",
                                 halign="right", size_hint_y=None, height=dp(45))
        self.hero.add_widget(self.hero_amount)
        self.hero_date = Label(text="", color=(.85,.96,.91,1), font_size="11sp", halign="right")
        self.hero.add_widget(self.hero_date)
        root.add_widget(self.hero)

        tabs = GridLayout(cols=4, spacing=dp(6), size_hint_y=None, height=dp(43))
        for key, label in [("day","اليوم"),("week","الأسبوع"),("month","الشهر"),("year","السنة")]:
            b = Button(text=label, font_size="12sp", bold=True, background_normal="",
                       background_color=GREEN if key == self.period else (1,1,1,1),
                       color=(1,1,1,1) if key == self.period else MUTED)
            b.bind(on_release=lambda btn, k=key: self.set_period(k))
            tabs.add_widget(b)
        self.tabs = tabs
        root.add_widget(tabs)

        date_nav = BoxLayout(size_hint_y=None, height=dp(43), spacing=dp(7))
        prev_btn = Button(text="‹ السابق", font_size="12sp", background_normal="",
                          background_color=(1,1,1,1), color=GREEN)
        prev_btn.bind(on_release=lambda *_: self.shift_date(-1))
        self.date_label = Label(text="", color=INK, bold=True, font_size="12sp")
        next_btn = Button(text="التالي ›", font_size="12sp", background_normal="",
                          background_color=(1,1,1,1), color=GREEN)
        next_btn.bind(on_release=lambda *_: self.shift_date(1))
        date_nav.add_widget(prev_btn); date_nav.add_widget(self.date_label); date_nav.add_widget(next_btn)
        root.add_widget(date_nav)

        stats = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(72))
        c1 = Card(orientation="vertical", radius=14)
        c1.add_widget(Label(text="عدد عمليات الشراء", color=MUTED, font_size="11sp", halign="right"))
        self.count_label = Label(text="0", color=INK, bold=True, font_size="18sp", halign="right")
        c1.add_widget(self.count_label)
        c2 = Card(orientation="vertical", radius=14)
        c2.add_widget(Label(text="إجمالي الفترة", color=MUTED, font_size="11sp", halign="right"))
        self.total_label = Label(text="0 دج", color=INK, bold=True, font_size="18sp", halign="right")
        c2.add_widget(self.total_label)
        stats.add_widget(c1); stats.add_widget(c2); root.add_widget(stats)

        form_card = Card(orientation="vertical", size_hint_y=None, height=dp(220), radius=18)
        form_card.add_widget(Label(text="إضافة مشتريات", color=INK, bold=True, font_size="17sp",
                                   halign="right", size_hint_y=None, height=dp(26)))
        form_card.add_widget(Label(text="أدخل تفاصيل الغرض الذي اشتريته", color=MUTED,
                                   font_size="11sp", halign="right", size_hint_y=None, height=dp(18)))
        self.name_input = TextInput(hint_text="اسم الغرض، مثلاً: خبز أو حليب", multiline=False,
                                    size_hint_y=None, height=dp(42), font_size="14sp",
                                    background_normal="", background_active="", background_color=(.98,1,.99,1),
                                    foreground_color=INK, padding=[dp(10),dp(10)])
        form_card.add_widget(self.name_input)
        row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self.price_input = TextInput(hint_text="السعر بالدينار", multiline=False, input_filter="float",
                                     font_size="13sp", background_normal="", background_active="",
                                     background_color=(.98,1,.99,1), foreground_color=INK,
                                     padding=[dp(8),dp(10)])
        self.qty_input = TextInput(text="1", hint_text="الكمية", multiline=False, input_filter="int",
                                   size_hint_x=.55, font_size="13sp", background_normal="",
                                   background_active="", background_color=(.98,1,.99,1),
                                   foreground_color=INK, padding=[dp(8),dp(10)])
        row.add_widget(self.price_input); row.add_widget(self.qty_input); form_card.add_widget(row)
        add_btn = Button(text="＋  إضافة المشتريات", size_hint_y=None, height=dp(43),
                         background_normal="", background_color=GREEN, color=(1,1,1,1),
                         bold=True, font_size="14sp")
        add_btn.bind(on_release=self.add_purchase)
        form_card.add_widget(add_btn)
        root.add_widget(form_card)

        list_header = BoxLayout(size_hint_y=None, height=dp(34))
        list_header.add_widget(Label(text="قائمة المشتريات", color=INK, bold=True, font_size="16sp", halign="right"))
        self.period_hint = Label(text="", color=MUTED, font_size="10sp", halign="left")
        list_header.add_widget(self.period_hint)
        root.add_widget(list_header)

        self.scroll = ScrollView(do_scroll_x=False, bar_width=dp(3))
        self.list_box = BoxLayout(orientation="vertical", spacing=dp(7), size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        self.scroll.add_widget(self.list_box)
        root.add_widget(self.scroll)

        self.refresh()
        return root

    def data_path(self):
        return os.path.join(self.user_data_dir, "purchases.json")

    def load_data(self):
        try:
            with open(self.data_path(), "r", encoding="utf-8") as f:
                self.purchases = json.load(f)
            if not isinstance(self.purchases, list): self.purchases = []
        except Exception:
            self.purchases = []

    def save_data(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        with open(self.data_path(), "w", encoding="utf-8") as f:
            json.dump(self.purchases, f, ensure_ascii=False, indent=2)

    def bounds(self):
        now = self.selected_date
        if self.period == "day":
            start = now; end = now + timedelta(days=1)
        elif self.period == "week":
            start = now - timedelta(days=now.weekday()); end = start + timedelta(days=7)
        elif self.period == "month":
            start = now.replace(day=1)
            end = date(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1)
        else:
            start = date(now.year,1,1); end = date(now.year+1,1,1)
        return start, end

    def selected_purchases(self):
        start, end = self.bounds()
        result = []
        for p in self.purchases:
            try:
                d = parse_dt(p["date"]).date()
                if start <= d < end: result.append(p)
            except Exception:
                pass
        return sorted(result, key=lambda p: p.get("date",""), reverse=True)

    def shift_date(self, amount):
        candidate = self.selected_date + timedelta(days=amount)
        if candidate <= date.today():
            self.selected_date = candidate
            self.refresh()

    def set_period(self, key):
        self.period = key
        for i, (k, _) in enumerate([("day","اليوم"),("week","الأسبوع"),("month","الشهر"),("year","السنة")]):
            btn = self.tabs.children[3-i]
            btn.background_color = GREEN if k == key else (1,1,1,1)
            btn.color = (1,1,1,1) if k == key else MUTED
        self.refresh()

    def add_purchase(self, *_):
        name = self.name_input.text.strip()
        try:
            price = float(self.price_input.text.replace(",", "."))
            qty = int(self.qty_input.text)
        except Exception:
            self.message("أدخل السعر والكمية بشكل صحيح.")
            return
        if not name or price < 0 or qty < 1:
            self.message("يرجى إدخال اسم وسعر وكمية صحيحة.")
            return
        self.purchases.append({"id": str(datetime.now().timestamp()), "name": name,
                               "price": price, "qty": qty, "date": datetime.now().isoformat(timespec="seconds")})
        self.save_data()
        self.name_input.text = ""; self.price_input.text = ""; self.qty_input.text = "1"
        self.refresh()

    def delete_purchase(self, item_id):
        box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        box.add_widget(Label(text="هل تريد حذف عملية الشراء هذه؟", color=INK))
        row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        popup = Popup(title="تأكيد الحذف", content=box, size_hint=(.82,.28))
        yes = Button(text="حذف", background_normal="", background_color=RED)
        no = Button(text="إلغاء", background_normal="", background_color=GREEN)
        row.add_widget(yes); row.add_widget(no); box.add_widget(row)
        yes.bind(on_release=lambda *_: (self._delete(item_id), popup.dismiss()))
        no.bind(on_release=popup.dismiss)
        popup.open()

    def _delete(self, item_id):
        self.purchases = [p for p in self.purchases if p.get("id") != item_id]
        self.save_data(); self.refresh()

    def message(self, text):
        Popup(title="مشترياتي", content=Label(text=text, color=INK),
              size_hint=(.82,.25)).open()

    def refresh(self):
        now = date.today()
        names = {"day":"اليوم","week":"هذا الأسبوع","month":"هذا الشهر","year":"هذه السنة"}
        self.hero.children[2].text = "إجمالي مشتريات " + names[self.period]
        self.hero_date.text = "التاريخ المحدد: " + self.selected_date.strftime("%Y-%m-%d")
        self.date_label.text = self.selected_date.strftime("%Y-%m-%d")
        now = self.selected_date
        items = self.selected_purchases()
        total = sum(float(p.get("price",0))*int(p.get("qty",1)) for p in items)
        self.hero_amount.text = fmt_money(total)
        self.count_label.text = str(len(items))
        self.total_label.text = fmt_money(total)
        hints = {"day":"من 00:00 إلى 00:00 غدًا","week":"الاثنين إلى الأحد",
                 "month":"من أول الشهر إلى أول الشهر التالي","year":"من يناير إلى يناير"}
        self.period_hint.text = hints[self.period]
        self.list_box.clear_widgets()
        if not items:
            empty = Label(text="لا توجد مشتريات في هذه الفترة.\nأضف أول عملية شراء من الأعلى.",
                          color=MUTED, font_size="13sp", size_hint_y=None, height=dp(95),
                          halign="center")
            self.list_box.add_widget(empty)
        else:
            for p in items:
                self.list_box.add_widget(PurchaseRow(p, self.delete_purchase))

if __name__ == "__main__":
    MoshtarayatiApp().run()
