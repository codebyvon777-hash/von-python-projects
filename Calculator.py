from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from functools import partial
import os
import hashlib
import requests
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp

symbol_map = {'÷': '//', '×': '*', '%': '/100'}

class ModernCalculatorApp(App):
    def build(self):
        self.layout = FloatLayout()
        self.last_result = ''
        self.last_expression = ''
        self.just_evaluated = False
        self.shading_enabled = True

        # Load shading preference  
        if os.path.exists("shading_pref.txt"):  
            with open("shading_pref.txt", "r") as f:  
                pref = f.read().strip()  
                self.shading_enabled = (pref == "ON")  

        # Background  
        self.bg = Image(source='', allow_stretch=True, keep_ratio=False)  
        with self.bg.canvas.before:  
            Color(0, 0, 0, 1)  
            self.rect = RoundedRectangle(size=self.bg.size, pos=self.bg.pos, radius=[0])  
            self.bg.bind(size=lambda instance, val: setattr(self.rect, 'size', instance.size))  
            self.bg.bind(pos=lambda instance, val: setattr(self.rect, 'pos', instance.pos))  
        self.layout.add_widget(self.bg)  

        # Load wallpaper if exists  
        if os.path.exists("wallpaper_path.txt"):  
            with open("wallpaper_path.txt", "r") as f:  
                path = f.read().strip()  
                if os.path.exists(path):  
                    self.bg.source = path  
                    self.bg.reload()  

        # Mode toggle buttons  
        self.calc_mode_btn = Button(text="Calculator", size_hint=(0.25, 0.08),  
                                    pos_hint={"x": 0.05, "y": 0.92},  
                                    background_normal='', background_color=(0,0,0,0.05))  
        self.calc_mode_btn.bind(on_press=self.show_calculator)  

        self.profit_mode_btn = Button(text="Profit Mode", size_hint=(0.25, 0.08),  
                                      pos_hint={"x": 0.70, "y": 0.92},  
                                      background_normal='', background_color=(0,0,0,0.05))  
        self.profit_mode_btn.bind(on_press=self.show_profit_mode)  

        self.layout.add_widget(self.calc_mode_btn)  
        self.layout.add_widget(self.profit_mode_btn)  

        # Wallpaper button  
        self.wallpaper_btn = Button(text="Wallpaper",  
                                    size_hint=(0.2, 0.08),  
                                    pos_hint={'x': 0.40, 'y': 0.92},  
                                    font_size=dp(18),  
                                    background_normal='',  
                                    background_color=(0, 0, 0, 0.05))  
        self.wallpaper_btn.bind(on_press=self.choose_wallpaper)  
        self.layout.add_widget(self.wallpaper_btn)  

        self.show_calculator()  
        return self.layout  

    def clear_mode_widgets(self):  
        keep = {self.bg, self.calc_mode_btn, self.profit_mode_btn, self.wallpaper_btn}  
        for widget in list(self.layout.children):  
            if widget not in keep:  
                self.layout.remove_widget(widget)  

    # ---------------- CALCULATOR MODE ----------------  
    def show_calculator(self, *args):  
        self.clear_mode_widgets()  

        # Entry field  
        self.entry = TextInput(size_hint=(0.9, 0.15),  
                               pos_hint={'x': 0.05, 'y': 0.78},  
                               font_size=dp(32),  
                               multiline=False,  
                               halign='right',  
                               background_color=(0.1, 0.1, 0.1, 0.4),  
                               foreground_color=(1, 1, 1, 1),  
                               padding=[dp(10), dp(10), dp(10), dp(10)])  
        self.entry.bind(text=self.update_preview)  
        self.layout.add_widget(self.entry)  

        # Shadow label  
        self.preview_shadow = Label(size_hint=(0.9, 0.15),  
                                    pos_hint={'x': 0.05, 'y': 0.78},  
                                    font_size=dp(28),  
                                    halign='right',  
                                    valign='middle',  
                                    color=(0, 0, 0, 0.5))  
        self.preview_shadow.bind(size=self.preview_shadow.setter('text_size'))  
        self.layout.add_widget(self.preview_shadow)  

        # Preview label  
        self.preview_label = Label(size_hint=(0.9, 0.15),  
                                   pos_hint={'x': 0.05, 'y': 0.78},  
                                   font_size=dp(28),  
                                   halign='right',  
                                   valign='middle',  
                                   color=(1, 1, 1, 0.8))  
        self.preview_label.bind(size=self.preview_label.setter('text_size'))  
        self.layout.add_widget(self.preview_label)  

        # Buttons  
        buttons = [  
            ('AC', 0.05, 0.63), ('X', 0.30, 0.63), ('%', 0.55, 0.63), ('÷', 0.80, 0.63),  
            ('7', 0.05, 0.50), ('8', 0.30, 0.50), ('9', 0.55, 0.50), ('×', 0.80, 0.50),  
            ('4', 0.05, 0.37), ('5', 0.30, 0.37), ('6', 0.55, 0.37), ('-', 0.80, 0.37),  
            ('1', 0.05, 0.24), ('2', 0.30, 0.24), ('3', 0.55, 0.24), ('+', 0.80, 0.24),  
            ('0', 0.05, 0.11), ('.', 0.30, 0.11), ('()', 0.55, 0.11), ('=', 0.80, 0.11)  
        ]  

        for text, x, y in buttons:  
            base_color = (0.1, 0.1, 0.1, 0.4)  
            if text == 'AC': base_color = (1, 0.5, 0, 0.5)  
            elif text == 'X': base_color = (1, 0, 0, 0.5)  
            elif text == '=': base_color = (0.2, 0.2, 0.2, 0.4)  

            btn = Button(text=text,  
                         size_hint=(0.2, 0.1),  
                         pos_hint={'x': x, 'y': y},  
                         font_size=dp(24),  
                         background_normal='',  
                         background_color=(0,0,0,0))  

            with btn.canvas.before:  
                if self.shading_enabled:  
                    Color(0, 0, 0, 0.6)  
                    RoundedRectangle(pos=btn.pos, size=btn.size, radius=[20])  
                btn.bg_color = Color(*base_color)  
                btn.rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[20])  

            btn.bind(pos=lambda instance, val, b=btn: setattr(b.rect, 'pos', instance.pos))  
            btn.bind(size=lambda instance, val, b=btn: setattr(b.rect, 'size', instance.size))  
            btn.bind(on_press=partial(self.button_press, btn))  
            btn.bind(on_release=partial(self.button_release, btn, text))  
            self.layout.add_widget(btn)  

    # ---------------- PROFIT MODE ----------------  
    def show_profit_mode(self, *args):  
        self.clear_mode_widgets()  
        self.cost_input = TextInput(hint_text="Cost", multiline=False,  
                                    size_hint=(0.8, 0.1), pos_hint={"x": 0.1, "y": 0.65})  
        self.roi_input = TextInput(hint_text="ROI %", multiline=False,  
                                   size_hint=(0.8, 0.1), pos_hint={"x": 0.1, "y": 0.52})  
        self.shipping_input = TextInput(hint_text="Shipping/Other", multiline=False,  
                                        size_hint=(0.8, 0.1), pos_hint={"x": 0.1, "y": 0.39})  
        self.layout.add_widget(self.cost_input)  
        self.layout.add_widget(self.roi_input)  
        self.layout.add_widget(self.shipping_input)  

        calc_btn = Button(text="Calculate Profit", size_hint=(0.6, 0.12),  
                          pos_hint={"x": 0.2, "y": 0.24},  
                          background_normal='', background_color=(0,0.5,0.2,0.6))  
        calc_btn.bind(on_press=self.calculate_profit_roi)  
        self.layout.add_widget(calc_btn)  

        self.profit_label = Label(text="Profit: $0.00 | Selling: $0.00", font_size=dp(28),  
                                  size_hint=(0.9, 0.15), pos_hint={"x": 0.05, "y": 0.05},  
                                  halign="center", valign="middle", color=(1,1,1,1))  
        self.profit_label.bind(size=self.profit_label.setter("text_size"))  
        self.layout.add_widget(self.profit_label)  

    def calculate_profit_roi(self, instance):  
        try:  
            cost = float(self.cost_input.text or 0)  
            roi = float(self.roi_input.text or 0)  
            shipping = float(self.shipping_input.text or 0)  
            selling_price = cost * (1 + roi / 100)  
            profit = selling_price - cost - shipping  
            # Add commas for thousands
            self.profit_label.text = f"Profit: ${profit:,.2f} | Selling: ${selling_price:,.2f}"  
        except:  
            self.profit_label.text = "Error"  

    # ---------------- CALCULATOR LOGIC ----------------  
    def button_press(self, button, instance):  
        r, g, b, a = button.bg_color.rgba  
        button.bg_color.rgba = (r*0.7, g*0.7, b*0.7, a)  

    def button_release(self, button, text, instance):  
        if text == 'AC':  
            button.bg_color.rgba = (1,0.5,0,0.5)  
            self.entry.text = ''  
        elif text == 'X':  
            button.bg_color.rgba = (1,0,0,0.5)  
            if self.entry.text:  
                self.entry.text = self.entry.text[:-1]  
            else:  
                self.entry.text = self.last_expression  
        elif text == '=':  
            button.bg_color.rgba = (0.2,0.2,0.2,0.4)  
            self.last_expression = self.entry.text  
            self.evaluate_secret()  
        elif text == '()':  
            open_count = self.entry.text.count('(')  
            close_count = self.entry.text.count(')')  
            if not self.entry.text or self.entry.text[-1] in '+-×÷%(':  
                self.entry.text += '('  
            elif self.entry.text[-1].isdigit() or self.entry.text[-1] == ')':  
                if open_count > close_count:  
                    self.entry.text += ')'  
                else:  
                    self.entry.text += '('  
        else:  
            if self.just_evaluated and (text.isdigit() or text == '.'):  
                self.entry.text = text  
                self.just_evaluated = False  
            else:  
                self.entry.text += text  
                self.just_evaluated = False  

    def update_preview(self, instance, value):  
        try:  
            expr = self.entry.text  
            for k, v in symbol_map.items():  
                expr = expr.replace(k, v)  
            result = eval(expr)
            # Add commas for thousands
            self.preview_label.text = f"{result:,}"  
        except:  
            self.preview_label.text = ''  

    # ---------------- SECRET EVAL ----------------  
    def evaluate_secret(self):  
        expr = self.entry.text.strip()  
        if expr.upper() == 'BTC':  
            self.entry.text = self.get_crypto('bitcoin')  
        elif expr.upper() == 'ETH':  
            self.entry.text = self.get_crypto('ethereum')  
        elif expr.upper().startswith('HASH '):  
            self.entry.text = hashlib.sha256(expr[5:].encode()).hexdigest()  
        elif expr.upper().startswith('ROI '):  
            try:  
                p,r,t = map(float, expr[4:].split())  
                self.entry.text = str(p*(1+r/100*t))  
            except:  
                self.entry.text = 'Error'  
        elif expr.upper() == 'NOTE':  
            self.open_secret_notes()  
        else:  
            self.entry.text = self.preview_label.text  
        self.just_evaluated = True  
        self.preview_label.text = ''  
        self.preview_shadow.text = ''  

    # ---------------- CRYPTO + NOTES ----------------  
    def get_crypto(self, coin):  
        try:  
            url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd'  
            r = requests.get(url).json()  
            return f"{r[coin]['usd']:,}"  # Add commas  
        except:  
            return 'API Error'  

    def open_secret_notes(self):  
        box = BoxLayout(orientation='vertical')  
        text = TextInput(text='', multiline=True, size_hint_y=None, height=300)  
        if os.path.exists("secret_notes.txt"):  
            with open("secret_notes.txt", "r") as f:  
                text.text = f.read()  
        box.add_widget(text)  
        save_btn = Button(text="Save", size_hint_y=None, height=50)  
        box.add_widget(save_btn)  
        popup = Popup(title="Secret Notes", content=box,  
                      size_hint=(0.8,0.6))  
        save_btn.bind(on_press=lambda x: self.save_notes(text.text, popup))  
        popup.open()  

    def save_notes(self, content, popup):  
        with open("secret_notes.txt","w") as f:  
            f.write(content)  
        popup.dismiss()  

    # ---------------- WALLPAPER ----------------  
    def choose_wallpaper(self, instance):  
        chooser = FileChooserIconView()  
        popup = Popup(title="Choose Wallpaper", content=chooser, size_hint=(0.9,0.9))  
        chooser.bind(on_submit=lambda chooser, selection, touch: self.set_wallpaper(selection, popup))  
        popup.open()  

    def set_wallpaper(self, selection, popup):  
        if selection:  
            path = selection[0]  
            self.bg.source = path  
            self.bg.reload()  
            # Save wallpaper path for persistence  
            with open("wallpaper_path.txt", "w") as f:  
                f.write(path)  
            popup.dismiss()


if __name__ == "__main__":
    ModernCalculatorApp().run()