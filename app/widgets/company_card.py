from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)
from PySide6.QtCore import Qt


class CompanyCard(QFrame):

    def __init__(self):
        super().__init__()

        self.setFrameShape(QFrame.StyledPanel)

        self.setStyleSheet("""
            QFrame{
                background-color:#23272e;
                border:1px solid #3c4048;
                border-radius:10px;
            }

            QLabel{
                color:white;
            }
        """)

        layout = QVBoxLayout(self)

        self.company = QLabel("Company Name")
        self.company.setAlignment(Qt.AlignLeft)

        self.company.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
            color:white;
        """)

        self.sector = QLabel("Sector")

        self.sector.setStyleSheet("""
            font-size:15px;
            color:#4FC3F7;
        """)

        self.industry = QLabel("Industry")

        self.industry.setStyleSheet("""
            font-size:13px;
            color:#BBBBBB;
        """)

        self.price = QLabel("Rs.  --")

        self.price.setStyleSheet("""
            font-size:22px;
            font-weight:bold;
            color:#00d084;
        """)

        self.marketcap = QLabel("Market Cap : --")

        self.marketcap.setStyleSheet("""
            font-size:15px;
            color:white;
        """)

        layout.addWidget(self.company)
        layout.addWidget(self.sector)
        layout.addWidget(self.industry)
        layout.addSpacing(10)
        layout.addWidget(self.price)
        layout.addWidget(self.marketcap)

    def updateData(
        self,
        company,
        sector,
        industry,
        price,
        marketcap,
    ):

        self.company.setText(company)
        self.sector.setText(sector)
        self.industry.setText(industry)
        self.price.setText(price)
        self.marketcap.setText(
            "Market Cap : " + marketcap
        )