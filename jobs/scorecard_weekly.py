from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import pandas as pd, os, datetime as dt

def run_scorecard(output_dir="snapshots"):
    os.makedirs(output_dir, exist_ok=True)
    date_str = dt.datetime.now().strftime("%Y-%m-%d")
    pdf_path = os.path.join(output_dir, f"Trade_Quality_Scorecard_{date_str}.pdf")
    xlsx_path = os.path.join(output_dir, f"Trade_Quality_Scorecard_{date_str}.xlsx")

    rows = [
        ["Ticker","Timing","Sizing","Risk Mgmt","Macro Alignment","Overall Grade","Lesson"],
        ["HPR.TO","B","C","B","B","B–","Scale down; diversify yield."],
        ["ZPR.TO","B","C","B","B","B–","Avoid overconcentration."],
        ["HSAV.TO","A","A","A","A","A","Keep defensive allocation."],
        ["CPD.TO","C","C","B","B","C+","Basket leaner now."],
        ["PET.TO","D","B","C","D","C–","Rotate before earnings/tariff."],
        ["DPM.TO","C","B","B","C","C+","Commodity patience; macro first."],
        ["ZEB.TO","C","B","B","B","B–","Re-entry when rates clarify."],
        ["RBC Bearings","C","B","B","C","C+","Check sector rotation."],
    ]

    styles=getSampleStyleSheet(); doc=SimpleDocTemplate(pdf_path, pagesize=letter)
    elements=[Paragraph("<b>Trade Quality Scorecard</b>", styles["Title"]),
              Paragraph(f"Date: {dt.datetime.now():%Y-%m-%d}", styles["Normal"]), Spacer(1,12)]
    t=Table(rows, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.grey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0),10),('BOTTOMPADDING',(0,0),(-1,0),8),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),('GRID',(0,0),(-1,-1),0.5,colors.black)
    ]))
    elements.append(t); doc.build(elements)

    df=pd.DataFrame(rows[1:], columns=rows[0]); df.to_excel(xlsx_path, index=False)
    return pdf_path, xlsx_path

if __name__=="__main__":
    run_scorecard()
