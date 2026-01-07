import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QSlider, QLabel
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath


# =========================
# Klasa Rura
# =========================
class Rura:
    def __init__(self, punkty, grubosc=12, kolor=Qt.gray):
        self.punkty = [QPointF(float(p[0]), float(p[1])) for p in punkty]
        self.grubosc = grubosc
        self.kolor_rury = kolor
        self.kolor_cieczy = QColor(0, 180, 255)
        self.czy_plynie = False

    def ustaw_przeplyw(self, plynie):
        self.czy_plynie = plynie

    def draw(self, painter):
        if len(self.punkty) < 2:
            return

        path = QPainterPath()
        path.moveTo(self.punkty[0])
        for p in self.punkty[1:]:
            path.lineTo(p)

        pen_rura = QPen(self.kolor_rury, self.grubosc,
                        Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen_rura)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        if self.czy_plynie:
            pen_ciecz = QPen(self.kolor_cieczy, self.grubosc - 4,
                             Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen_ciecz)
            painter.drawPath(path)


# =========================
# Klasa Zbiornik
# =========================
class Zbiornik:
    def __init__(self, x, y, width=100, height=140, nazwa=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.nazwa = nazwa

        self.pojemnosc = 100.0
        self.aktualna_ilosc = 0.0
        self.poziom = 0.0
        self.alarm = False

    def dodaj_ciecz(self, ilosc):
        wolne = self.pojemnosc - self.aktualna_ilosc
        dodano = min(ilosc, wolne)
        self.aktualna_ilosc += dodano
        self.aktualizuj_poziom()
        return dodano

    def usun_ciecz(self, ilosc):
        usunieto = min(ilosc, self.aktualna_ilosc)
        self.aktualna_ilosc -= usunieto
        self.aktualizuj_poziom()
        return usunieto

    def aktualizuj_poziom(self):
        self.poziom = self.aktualna_ilosc / self.pojemnosc
        self.alarm = self.aktualna_ilosc >= self.pojemnosc - 0.1

    def czy_pusty(self):
        return self.aktualna_ilosc <= 0.1

    def czy_pelny(self):
        return self.alarm

    def punkt_gora_srodek(self):
        return (self.x + self.width / 2, self.y)

    def punkt_dol_srodek(self):
        return (self.x + self.width / 2, self.y + self.height)

    def draw(self, painter):
        if self.poziom > 0:
            h = self.height * self.poziom
            y = self.y + self.height - h
            painter.setPen(Qt.NoPen)
            painter.setBrush(
                QColor(255, 80, 80, 220) if self.alarm
                else QColor(0, 120, 255, 200)
            )
            painter.drawRect(
                int(self.x + 3),
                int(y),
                int(self.width - 6),
                int(h - 2)
            )

        painter.setPen(QPen(Qt.white, 4))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(
            int(self.x),
            int(self.y),
            int(self.width),
            int(self.height)
        )

        painter.setPen(Qt.white)
        painter.drawText(int(self.x), int(self.y - 10), self.nazwa)

        if self.alarm:
            painter.drawText(
                int(self.x),
                int(self.y + self.height + 20),
                "PEŁNE"
            )


# =========================
# Główna Symulacja
# =========================
class SymulacjaKaskady(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Symulacja kaskadowa – 4 zbiorniki")
        self.setFixedSize(1000, 700)
        self.setStyleSheet("background-color: #222;")

        self.z1 = Zbiornik(450, 30, nazwa="Zbiornik 1")
        self.z1.aktualna_ilosc = 100.0
        self.z1.aktualizuj_poziom()

        self.z2 = Zbiornik(450, 220, nazwa="Zbiornik 2")
        self.z3 = Zbiornik(200, 400, nazwa="Zbiornik 3")
        self.z4 = Zbiornik(700, 400, nazwa="Zbiornik 4")

        self.zbiorniki = [self.z1, self.z2, self.z3, self.z4]

        self.rury = []
        self._stworz_rury()
        self.rura_z2_z4 = self._stworz_rure_z2_z4()

        self.timer = QTimer()
        self.timer.timeout.connect(self.logika_przeplywu)

        self.running = False
        self.flow_speed = 0.8

        self._stworz_przyciski()

        self.flow_multipliers = [1.0, 1.0, 1.0]
        self._dodaj_kontrole_przeplywu()

    def _stworz_rury(self):
        for a, b in zip(self.zbiorniki[:2], self.zbiorniki[1:3]):
            ps = a.punkt_dol_srodek()
            pk = b.punkt_gora_srodek()
            mid = ps[1] + 60

            self.rury.append(Rura([
                ps,
                (ps[0], mid),
                (pk[0], mid),
                pk
            ]))

    def _stworz_rure_z2_z4(self):
        ps = self.z2.punkt_dol_srodek()
        pk = self.z4.punkt_gora_srodek()
        mid = ps[1] + 60

        return Rura([
            ps,
            (ps[0], mid),
            (pk[0], mid),
            pk
        ])

    def _stworz_przyciski(self):
        y = 660
        x = 50

        self.btn_start = QPushButton("Start / Stop", self)
        self.btn_start.setGeometry(x, y, 120, 30)
        self.btn_start.setStyleSheet("color: white;")
        self.btn_start.clicked.connect(self.przelacz_symulacje)

        x += 150
        for i, z in enumerate(self.zbiorniki, start=1):
            b_plus = QPushButton(f"Z{i} +", self)
            b_minus = QPushButton(f"Z{i} -", self)

            b_plus.setGeometry(x, y, 60, 30)
            b_minus.setGeometry(x + 65, y, 60, 30)

            b_plus.setStyleSheet("color: white;")
            b_minus.setStyleSheet("color: white;")

            b_plus.clicked.connect(lambda _, zb=z: self.napelnij(zb))
            b_minus.clicked.connect(lambda _, zb=z: self.oproznij(zb))

            x += 140

    def _dodaj_kontrole_przeplywu(self):
        x = 50
        y = 560

        for i in range(2):  
            lbl = QLabel(f"Przepływ Z{i+1}", self)
            lbl.setStyleSheet("color: white;")
            lbl.setGeometry(x, y, 120, 20)

            slider = QSlider(Qt.Horizontal, self)
            slider.setGeometry(x + 130, y, 150, 20)
            slider.setRange(10, 200)
            slider.setValue(100)
            slider.valueChanged.connect(
                lambda v, idx=i: self.ustaw_przeplyw(idx, v)
            )
            y += 30

    def ustaw_przeplyw(self, idx, value):
        self.flow_multipliers[idx] = value / 100.0

    def napelnij(self, zb):
        zb.aktualna_ilosc = zb.pojemnosc
        zb.aktualizuj_poziom()
        self.update()

    def oproznij(self, zb):
        zb.aktualna_ilosc = 0.0
        zb.aktualizuj_poziom()
        self.update()

    def przelacz_symulacje(self):
        if self.running:
            self.timer.stop()
        else:
            self.timer.start(20)
        self.running = not self.running

    def logika_przeplywu(self):
        if not self.z1.czy_pusty() and not self.z2.czy_pelny():
            il = self.z1.usun_ciecz(self.flow_speed * self.flow_multipliers[0])
            self.z2.dodaj_ciecz(il)
            self.rury[0].ustaw_przeplyw(True)
        else:
            self.rury[0].ustaw_przeplyw(False)

        if not self.z2.czy_pusty():
            il = self.flow_speed * self.flow_multipliers[1] / 2

            if not self.z3.czy_pelny():
                self.z3.dodaj_ciecz(self.z2.usun_ciecz(il))
                self.rury[1].ustaw_przeplyw(True)
            else:
                self.rury[1].ustaw_przeplyw(False)

            if not self.z4.czy_pelny():
                self.z4.dodaj_ciecz(self.z2.usun_ciecz(il))
                self.rura_z2_z4.ustaw_przeplyw(True)
            else:
                self.rura_z2_z4.ustaw_przeplyw(False)

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for r in self.rury:
            r.draw(p)
        self.rura_z2_z4.draw(p)
        for z in self.zbiorniki:
            z.draw(p)


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    okno = SymulacjaKaskady()
    okno.show()
    sys.exit(app.exec_())
