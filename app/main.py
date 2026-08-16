import tkinter as tk
from datetime import datetime

BG = '#0B1114'
CARD = '#151D21'
EDGE = '#2B353A'
CREAM = '#F3EBDD'
GREEN = '#91A961'
GREEN_DARK = '#26352B'
ORANGE = '#F39A18'
MUTED = '#AEB8B3'

AGENDA = [
    ('10:00', 'Tandartscontrole', 'Johan'),
    ('14:30', 'Boodschappen doen', ''),
    ('16:00', 'Sporten', 'Emma'),
    ('19:30', 'Avondeten met familie', ''),
]
TASKS = [
    ['Vuilnis buitenzetten', True],
    ['Boodschappen halen', False],
    ['Was opvouwen', False],
    ['Auto tanken', False],
    ['Bloemen water geven', False],
]
DAYS = ['maandag','dinsdag','woensdag','donderdag','vrijdag','zaterdag','zondag']
MONTHS = ['januari','februari','maart','april','mei','juni','juli','augustus','september','oktober','november','december']

class TuusDemo:
    def __init__(self, root):
        self.root = root
        root.title('Tuus')
        root.attributes('-fullscreen', True)
        root.configure(bg=BG)
        root.bind('<Escape>', lambda e: root.destroy())

        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.task_vars = []
        self.draw_layout()
        self.update_clock()

    def rounded_rect(self, x1, y1, x2, y2, radius=24, **kw):
        p = [x1+radius,y1, x2-radius,y1, x2,y1, x2,y1+radius,
             x2,y2-radius, x2,y2, x2-radius,y2, x1+radius,y2,
             x1,y2, x1,y2-radius, x1,y1+radius, x1,y1]
        return self.canvas.create_polygon(p, smooth=True, splinesteps=24, **kw)

    def draw_layout(self):
        self.root.update_idletasks()
        w = self.root.winfo_screenwidth(); h = self.root.winfo_screenheight()
        m = int(w*0.025); gap = int(w*0.018); top = int(h*0.12); footer = int(h*0.055)
        bottom = h-footer; cw = (w-2*m-gap)/2; ch = (bottom-top-gap)/2
        lx1, lx2 = m, m+cw; rx1, rx2 = lx2+gap, w-m
        ty1, ty2 = top, top+ch; by1, by2 = ty2+gap, bottom

        self.canvas.create_text(w/2, h*0.035, text='TUUS', fill=CREAM,
                                font=('DejaVu Sans', int(h*0.052), 'bold'))
        self.canvas.create_text(w/2, h*0.087, text='Welkom thuis', fill=GREEN,
                                font=('DejaVu Sans', int(h*0.024)))
        for c in [(lx1,ty1,lx2,ty2),(rx1,ty1,rx2,ty2),(lx1,by1,lx2,by2),(rx1,by1,rx2,by2)]:
            self.rounded_rect(*c, fill=CARD, outline=EDGE, width=2)

        self.draw_agenda(lx1,ty1,lx2,ty2)
        self.draw_clock(rx1,ty1,rx2,ty2)
        self.draw_tasks(lx1,by1,lx2,by2)
        self.draw_weather(rx1,by1,rx2,by2)
        self.canvas.create_text(w/2, h-footer/2, text='TUUS v0.2', fill=GREEN,
                                font=('DejaVu Sans', int(h*0.018)))

    def title_block(self, x1, y1, symbol, title):
        self.canvas.create_oval(x1+34,y1+22,x1+96,y1+84,fill=GREEN_DARK,outline='')
        self.canvas.create_text(x1+65,y1+53,text=symbol,fill=CREAM,font=('DejaVu Sans',27,'bold'))
        self.canvas.create_text(x1+126,y1+50,anchor='w',text=title,fill=GREEN,
                                font=('DejaVu Sans',28,'bold'))

    def draw_agenda(self, x1,y1,x2,y2):
        self.title_block(x1,y1,'▣','AGENDA')
        now=datetime.now(); dt=f"{DAYS[now.weekday()]} {now.day} {MONTHS[now.month-1]} {now.year}"
        self.canvas.create_text(x1+126,y1+84,anchor='w',text=dt.capitalize(),fill=GREEN,
                                font=('DejaVu Sans',18))
        sy=y1+130; rh=58
        self.canvas.create_line(x1+52,sy-10,x1+52,sy+rh*len(AGENDA)-12,fill=ORANGE,width=3)
        for i,(t,title,owner) in enumerate(AGENDA):
            cy=sy+i*rh
            self.canvas.create_text(x1+78,cy,anchor='w',text=t,fill=ORANGE,font=('DejaVu Sans',20,'bold'))
            self.canvas.create_text(x1+190,cy-(7 if owner else 0),anchor='w',text=title,fill=CREAM,font=('DejaVu Sans',20))
            if owner:
                self.canvas.create_text(x1+190,cy+18,anchor='w',text=owner,fill=GREEN,font=('DejaVu Sans',14))
            if i<len(AGENDA)-1:
                self.canvas.create_line(x1+175,cy+30,x2-34,cy+30,fill='#2A3337')
        self.canvas.create_text(x1+34,y2-28,anchor='w',text='Morgen:   09:00   Werkoverleg',fill=GREEN,font=('DejaVu Sans',17))

    def draw_clock(self,x1,y1,x2,y2):
        cx=(x1+x2)/2
        self.clock_text=self.canvas.create_text(cx+35,y1+130,text='--:--',fill=ORANGE,font=('DejaVu Sans',92,'bold'))
        self.date_text=self.canvas.create_text(cx,y1+232,text='',fill=CREAM,font=('DejaVu Sans',24))
        self.canvas.create_line(x1+30,y1+282,x2-30,y1+282,fill='#2A3337',width=2)
        self.canvas.create_text(cx,y2-40,text='⌂   Fijn dat je er bent!',fill=GREEN,font=('DejaVu Sans',18))

    def draw_tasks(self,x1,y1,x2,y2):
        self.title_block(x1,y1,'✓','TO DO')
        sy=y1+118
        for i,(name,done) in enumerate(TASKS):
            var=tk.BooleanVar(value=done); self.task_vars.append(var)
            cb=tk.Checkbutton(self.root,text=name,variable=var,command=self.update_task_count,
                              bg=CARD,fg=CREAM,activebackground=CARD,activeforeground=CREAM,
                              selectcolor=GREEN_DARK,font=('DejaVu Sans',18),anchor='w',bd=0,
                              highlightthickness=0)
            self.canvas.create_window(x1+55,sy+i*48,anchor='w',window=cb,width=(x2-x1)-90,height=40)
        self.canvas.create_line(x1+34,y2-66,x2-34,y2-66,fill='#2A3337')
        self.task_count_text=self.canvas.create_text(x1+34,y2-32,anchor='w',text='',fill=GREEN,font=('DejaVu Sans',16))
        self.update_task_count()

    def draw_weather(self,x1,y1,x2,y2):
        self.title_block(x1,y1,'☀','WEER')
        self.canvas.create_text(x1+112,y1+138,text='21°C',fill=ORANGE,font=('DejaVu Sans',48,'bold'))
        self.canvas.create_text(x1+112,y1+192,text='Zonnig',fill=CREAM,font=('DejaVu Sans',21))
        for i,text in enumerate(['Voelt als 21°C','ZW 13 km/u','Vochtigheid 59%']):
            yy=y1+248+i*48
            self.canvas.create_text(x1+40,yy,anchor='w',text='•',fill=GREEN,font=('DejaVu Sans',24,'bold'))
            self.canvas.create_text(x1+92,yy,anchor='w',text=text,fill=CREAM,font=('DejaVu Sans',17))
        rx1=x1+(x2-x1)*0.43; ry1=y1+24; rx2=x2-18; ry2=y2-18
        self.rounded_rect(rx1,ry1,rx2,ry2,fill='#203B43',outline='#355661',width=2)
        self.canvas.create_text((rx1+rx2)/2,(ry1+ry2)/2-24,text='BUIENRADAR',fill=CREAM,font=('DejaVu Sans',25,'bold'))
        self.canvas.create_text((rx1+rx2)/2,(ry1+ry2)/2+20,text='live kaart volgt',fill=MUTED,font=('DejaVu Sans',17))
        for i in range(7):
            x=rx1+55+i*42
            self.canvas.create_oval(x,ry1+68+(i%3)*35,x+22,ry1+90+(i%3)*35,fill='#4B80C9',outline='')

    def update_clock(self):
        now=datetime.now()
        self.canvas.itemconfigure(self.clock_text,text=now.strftime('%H:%M'))
        dt=f"{DAYS[now.weekday()].capitalize()} {now.day} {MONTHS[now.month-1]} {now.year}"
        self.canvas.itemconfigure(self.date_text,text=dt)
        self.root.after(1000,self.update_clock)

    def update_task_count(self):
        n=sum(v.get() for v in self.task_vars)
        self.canvas.itemconfigure(self.task_count_text,text=f'✓  {n} van {len(self.task_vars)} taken voltooid')

if __name__ == '__main__':
    root=tk.Tk(); TuusDemo(root); root.mainloop()
