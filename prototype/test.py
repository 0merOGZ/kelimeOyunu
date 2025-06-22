import pyodbc
import random
import time
import os
import tkinter as tk
from tkinter import messagebox, font


server = 'localhost'
database = 'kelimeOyunu'

try:
    conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;')
    cursor = conn.cursor()


    cursor.execute("SELECT kelime, aciklama, detayli FROM kelimeler WHERE zorluk = 'kolay' ORDER BY NEWID()")
    kolay_kelime = cursor.fetchmany(3)

    cursor.execute("SELECT kelime, aciklama, detayli FROM kelimeler WHERE zorluk = 'orta' ORDER BY NEWID()")
    orta_kelime = cursor.fetchmany(4)

    cursor.execute("SELECT kelime, aciklama, detayli FROM kelimeler WHERE zorluk = 'zor' ORDER BY NEWID()")
    zor_kelime = cursor.fetchmany(3)

    conn.close()

except Exception as e:
    print(f"Veritabanı bağlantı hatası: {e}")
    exit()


class KelimeOyunuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kelime Tahmin Oyunu")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Oyun verileri
        self.tum_kelimeler = kolay_kelime + orta_kelime + zor_kelime
        random.shuffle(self.tum_kelimeler)
        self.puan = 0
        self.oyun_suresi = 200
        self.baslangic_zamani = None
        self.kalan_sure = self.oyun_suresi
        self.suanki_kelime_index = 0
        self.acik_harfler = set()
        self.joker1_hak = 3
        self.joker2_hak = 1
        self.kelime_puani = 100
        self.timer_running = False
        
        # Fontlar
        self.baslik_font = font.Font(family="Arial", size=16, weight="bold")
        self.normal_font = font.Font(family="Arial", size=12)
        self.kelime_font = font.Font(family="Courier", size=16, weight="bold")
        
        # Ana frame
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        self.baslik_frame = tk.Frame(self.main_frame, bg="#4a7abc", padx=10, pady=10)
        self.baslik_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.baslik_label = tk.Label(self.baslik_frame, text="KELİME TAHMİN OYUNU", 
                                    font=self.baslik_font, bg="#4a7abc", fg="white")
        self.baslik_label.pack()
        
        # Bilgi frame
        self.bilgi_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.bilgi_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.kelime_index_label = tk.Label(self.bilgi_frame, text="Kelime: 0/10", 
                                         font=self.normal_font, bg="#f0f0f0")
        self.kelime_index_label.pack(side=tk.LEFT, padx=5)
        
        self.sure_label = tk.Label(self.bilgi_frame, text=f"Kalan Süre: {self.kalan_sure}s", 
                                  font=self.normal_font, bg="#f0f0f0")
        self.sure_label.pack(side=tk.LEFT, padx=5)
        
        self.puan_label = tk.Label(self.bilgi_frame, text=f"Puan: {self.puan}", 
                                  font=self.normal_font, bg="#f0f0f0")
        self.puan_label.pack(side=tk.LEFT, padx=5)
        
        self.uzunluk_label = tk.Label(self.bilgi_frame, text="Kelime Uzunluğu: 0 harf", 
                                     font=self.normal_font, bg="#f0f0f0")
        self.uzunluk_label.pack(side=tk.LEFT, padx=5)
        
        # Açıklama frame
        self.aciklama_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.aciklama_frame.pack(fill=tk.X, pady=10)
        
        self.aciklama_label = tk.Label(self.aciklama_frame, text="Açıklama: ", 
                                      font=self.normal_font, bg="#f0f0f0", wraplength=750, justify=tk.LEFT)
        self.aciklama_label.pack(anchor=tk.W)
        
        # Kelime gösterim frame
        self.kelime_frame = tk.Frame(self.main_frame, bg="#e6e6e6", pady=20)
        self.kelime_frame.pack(fill=tk.X, pady=10)
        
        self.kelime_label = tk.Label(self.kelime_frame, text="", font=self.kelime_font, bg="#e6e6e6")
        self.kelime_label.pack()
        
        # Joker frame
        self.joker_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.joker_frame.pack(fill=tk.X, pady=10)
        
        self.joker1_btn = tk.Button(self.joker_frame, text="Harf Al (3/3)", font=self.normal_font,
                                   command=self.joker_harf_al, width=15, bg="#4CAF50", fg="white")
        self.joker1_btn.pack(side=tk.LEFT, padx=5)
        
        self.joker2_btn = tk.Button(self.joker_frame, text="Detay Aç (1/1)", font=self.normal_font,
                                   command=self.joker_detay_ac, width=15, bg="#2196F3", fg="white")
        self.joker2_btn.pack(side=tk.LEFT, padx=5)
        
        # Tahmin frame
        self.tahmin_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.tahmin_frame.pack(fill=tk.X, pady=10)
        
        self.tahmin_label = tk.Label(self.tahmin_frame, text="Tahmininiz:", 
                                    font=self.normal_font, bg="#f0f0f0")
        self.tahmin_label.pack(side=tk.LEFT, padx=5)
        
        self.tahmin_entry = tk.Entry(self.tahmin_frame, font=self.normal_font, width=30)
        self.tahmin_entry.pack(side=tk.LEFT, padx=5)
        self.tahmin_entry.bind("<Return>", self.tahmin_yap)
        
        self.tahmin_btn = tk.Button(self.tahmin_frame, text="Tahmin Et", font=self.normal_font,
                                   command=self.tahmin_yap, bg="#FF5722", fg="white")
        self.tahmin_btn.pack(side=tk.LEFT, padx=5)
        
        # Sonuç mesajı
        self.sonuc_label = tk.Label(self.main_frame, text="", font=self.baslik_font, bg="#f0f0f0")
        self.sonuc_label.pack(pady=20)
        
        # Başla butonu
        self.basla_btn = tk.Button(self.main_frame, text="OYUNU BAŞLAT", font=self.baslik_font,
                                  command=self.oyunu_baslat, bg="#4a7abc", fg="white", padx=20, pady=10)
        self.basla_btn.pack(pady=20)
    
    def oyunu_baslat(self):
        self.baslangic_zamani = time.time()
        self.puan = 0
        self.suanki_kelime_index = 0
        self.basla_btn.pack_forget()
        self.sonuc_label.config(text="")
        self.update_timer()
        self.sonraki_kelime()
        self.timer_running = True
    
    def update_timer(self):
        if not self.timer_running:
            return
            
        gecen_sure = time.time() - self.baslangic_zamani
        self.kalan_sure = max(0, self.oyun_suresi - int(gecen_sure))
        self.sure_label.config(text=f"Kalan Süre: {self.kalan_sure}s")
        
        if self.kalan_sure <= 0:
            self.oyun_bitti("ZAMAN DOLDU!")
        else:
            self.root.after(1000, self.update_timer)
    
    def sonraki_kelime(self):
        if self.suanki_kelime_index >= len(self.tum_kelimeler):
            self.oyun_bitti("TÜM KELİMELER TAMAMLANDI!")
            return
            
        kelime, aciklama, detayli = self.tum_kelimeler[self.suanki_kelime_index]
        self.kelime_index_label.config(text=f"Kelime: {self.suanki_kelime_index + 1}/10")
        self.aciklama_label.config(text=f"Açıklama: {aciklama}")
        self.uzunluk_label.config(text=f"Kelime Uzunluğu: {len(kelime)} harf")
        
        self.acik_harfler = set()
        self.joker1_hak = 3
        self.joker2_hak = 1
        self.kelime_puani = 100
        self.joker1_btn.config(text=f"Harf Al ({self.joker1_hak}/3)", state=tk.NORMAL)
        self.joker2_btn.config(text=f"Detay Aç ({self.joker2_hak}/1)", state=tk.NORMAL)
        
        self.update_kelime_display()
        self.tahmin_entry.delete(0, tk.END)
        self.tahmin_entry.focus()
    
    def update_kelime_display(self):
        kelime = self.tum_kelimeler[self.suanki_kelime_index][0]
        gosterim = ' '.join([h if h in self.acik_harfler else '_' for h in kelime])
        self.kelime_label.config(text=gosterim)
    
    def joker_harf_al(self):
        if self.joker1_hak <= 0:
            return
            
        kelime = self.tum_kelimeler[self.suanki_kelime_index][0]
        kapali_harfler = [h for h in kelime if h not in self.acik_harfler]
        
        if kapali_harfler:
            yeni_harf = random.choice(kapali_harfler)
            self.acik_harfler.add(yeni_harf)
            self.joker1_hak -= 1
            self.kelime_puani -= 20
            self.joker1_btn.config(text=f"Harf Al ({self.joker1_hak}/3)")
            self.update_kelime_display()
            messagebox.showinfo("Joker - Harf", f"Yeni harf: '{yeni_harf}'\nKelime puanı: {self.kelime_puani}")
        else:
            messagebox.showinfo("Joker - Harf", "Tüm harfler zaten açık!")
    
    def joker_detay_ac(self):
        if self.joker2_hak <= 0:
            return
            
        detayli = self.tum_kelimeler[self.suanki_kelime_index][2]
        self.joker2_hak -= 1
        self.kelime_puani = self.kelime_puani // 2
        self.joker2_btn.config(text=f"Detay Aç ({self.joker2_hak}/1)")
        messagebox.showinfo("Joker - Detay", f"Detaylı Açıklama:\n{detayli}\n\nKelime puanı yarıya düşürüldü: {self.kelime_puani}")
    
    def tahmin_yap(self, event=None):
        tahmin = self.tahmin_entry.get().strip().lower()
        if not tahmin:
            return
            
        kelime = self.tum_kelimeler[self.suanki_kelime_index][0]
        
        if tahmin == kelime:
            self.puan += self.kelime_puani
            self.puan_label.config(text=f"Puan: {self.puan}")
            self.sonuc_label.config(text=f"TEBRİKLER! Doğru Tahmin: {kelime.upper()}", fg="green")
            
            self.tahmin_entry.config(state=tk.DISABLED)
            self.tahmin_btn.config(state=tk.DISABLED)
            self.joker1_btn.config(state=tk.DISABLED)
            self.joker2_btn.config(state=tk.DISABLED)
            
            self.root.after(2000, self.kelime_tamamlandi)
        else:
            self.sonuc_label.config(text="Yanlış tahmin! Tekrar deneyin.", fg="red")
            self.tahmin_entry.delete(0, tk.END)
    
    def kelime_tamamlandi(self):
        self.suanki_kelime_index += 1
        self.sonuc_label.config(text="")
        self.tahmin_entry.config(state=tk.NORMAL)
        self.tahmin_btn.config(state=tk.NORMAL)
        self.sonraki_kelime()
    
    def oyun_bitti(self, mesaj):
        self.timer_running = False
        self.sonuc_label.config(text=mesaj, fg="blue")
        
        # Oyun sonu penceresi göster
        skor_mesaji = f"OYUN SONU - TOPLAM PUAN: {self.puan}\n\n"
        
        if self.puan >= 800:
            skor_mesaji += "★★★★★ MÜKEMMEL! Harika bir skor!"
        elif self.puan >= 600:
            skor_mesaji += "★★★★☆ ÇOK İYİ! Biraz daha çalışmalısın."
        elif self.puan >= 400:
            skor_mesaji += "★★★☆☆ İYİ! Orta seviye skor."
        else:
            skor_mesaji += "★★☆☆☆ DAHA İYİSİNİ YAPABİLİRSİN!"
        
        messagebox.showinfo("Oyun Sonu", skor_mesaji)
        
        # Yeniden başlatma butonu göster
        self.basla_btn.config(text="YENİDEN BAŞLAT")
        self.basla_btn.pack(pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    app = KelimeOyunuApp(root)
    root.mainloop()