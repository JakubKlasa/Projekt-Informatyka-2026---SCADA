import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
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

        # Obudowa rury
        pen_rura = QPen(self.kolor_rury, self.grubosc, Qt.SolidLine,
                        Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen_rura)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Ciecz
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

    def czy_pusty(self):
        return self.aktualna_ilosc <= 0.1

    def czy_pelny(self):
        return self.aktualna_ilosc >= self.pojemnosc - 0.1

    def punkt_gora_srodek(self):
        return (self.x + self.width / 2, self.y)

    def punkt_dol_srodek(self):
        return (self.x + self.width / 2, self.y + self.height)

    def draw(self, painter):
        # Ciecz
        if self.poziom > 0:
            h_cieczy = self.height * self.poziom
            y_start = self.y + self.height - h_cieczy
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 120, 255, 200))
            painter.drawRect(
                int(self.x + 3),
                int(y_start),
                int(self.width - 6),
                int(h_cieczy - 2)
            )

        # Obrys
        pen = QPen(Qt.white, 4)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(
            int(self.x),
            int(self.y),
            int(self.width),
            int(self.height)
        )

        # Nazwa
        painter.setPen(Qt.white)
        painter.drawText(int(self.x), int(self.y - 10), self.nazwa)


# =========================
# Główna Symulacja
# =========================
class SymulacjaKaskady(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Symulacja kaskadowa – 4 zbiorniki")
        self.setFixedSize(1000, 650)
        self.setStyleSheet("background-color: #222;")

        # Zbiorniki
        self.z1 = Zbiornik(50, 50, nazwa="Zbiornik 1")
        self.z1.aktualna_ilosc = 100.0
        self.z1.aktualizuj_poziom()

        self.z2 = Zbiornik(300, 200, nazwa="Zbiornik 2")
        self.z3 = Zbiornik(550, 350, nazwa="Zbiornik 3")
        self.z4 = Zbiornik(800, 500, nazwa="Zbiornik 4")

        self.zbiorniki = [self.z1, self.z2, self.z3, self.z4]

        # Rury
        self.rury = []
        self._stworz_rury()

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.logika_przeplywu)

        self.btn = QPushButton("Start / Stop", self)
        self.btn.setGeometry(50, 600, 120, 30)
        self.btn.setStyleSheet("background-color: #444; color: white;")
        self.btn.clicked.connect(self.przelacz_symulacje)

        self.running = False
        self.flow_speed = 0.8

    def _stworz_rury(self):
        pary = [
            (self.z1, self.z2),
            (self.z2, self.z3),
            (self.z3, self.z4)
        ]

        for z_a, z_b in pary:
            p_start = z_a.punkt_dol_srodek()
            p_end = z_b.punkt_gora_srodek()
            mid_y = (p_start[1] + p_end[1]) / 2

            rura = Rura([
                p_start,
                (p_start[0], mid_y),
                (p_end[0], mid_y),
                p_end
            ])
            self.rury.append(rura)

    def przelacz_symulacje(self):
        if self.running:
            self.timer.stop()
        else:
            self.timer.start(20)
        self.running = not self.running

    def logika_przeplywu(self):
        for i in range(len(self.zbiorniki) - 1):
            z_gora = self.zbiorniki[i]
            z_dol = self.zbiorniki[i + 1]
            rura = self.rury[i]

            plynie = False
            if not z_gora.czy_pusty() and not z_dol.czy_pelny():
                ilosc = z_gora.usun_ciecz(self.flow_speed)
                z_dol.dodaj_ciecz(ilosc)
                plynie = True

            rura.ustaw_przeplyw(plynie)

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        for r in self.rury:
            r.draw(p)
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
