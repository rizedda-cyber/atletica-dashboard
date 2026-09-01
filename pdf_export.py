"""
pdf_export.py — Generazione del PDF del programma settimanale.

Prende le righe della griglia "Programma" (prima ancora di essere salvate
come assegnazioni vere) e produce un PDF pronto da mandare su WhatsApp,
nello stesso spirito dei PDF che il coach gia' scrive a mano: giorni in
grassetto, blocchi elencati sotto.
"""

import pandas as pd
from fpdf import FPDF

GIORNI_ORDINE = ["Lunedi", "Martedi", "Mercoledi", "Giovedi", "Venerdi", "Sabato", "Domenica"]
GIORNI_ORDINE_ACCENTATO = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

# Il font base di fpdf2 (Helvetica) supporta solo latin-1: caratteri tipici
# di un copia-incolla da Word (trattini lunghi, virgolette curve) altrimenti
# fanno fallire l'export. Li normalizziamo, e in ultima istanza sostituiamo
# qualunque carattere residuo non rappresentabile invece di far crashare
# il download.
_SOSTITUZIONI = {
    "—": "-", "–": "-",   # em/en dash
    "‘": "'", "’": "'",   # apici curvi
    "“": '"', "”": '"',   # virgolette curve
    "…": "...",                # puntini di sospensione
}


def _pdf_safe(testo: str) -> str:
    for orig, sost in _SOSTITUZIONI.items():
        testo = testo.replace(orig, sost)
    return testo.encode("latin-1", errors="replace").decode("latin-1")


def _nome_giorno(data) -> str:
    ts = pd.Timestamp(data)
    idx = ts.weekday()  # 0 = lunedi
    return f"{GIORNI_ORDINE[idx]} {ts.strftime('%d/%m')}"


def genera_pdf_settimana(df_blocchi: pd.DataFrame, titolo: str = "Programma Settimanale") -> bytes:
    """
    df_blocchi deve avere le colonne: Giorno (data), Tipo sessione,
    Descrizione, Target (puo' essere vuoto), Assegna a.
    Restituisce i bytes del PDF.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, _pdf_safe(titolo), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    if df_blocchi.empty:
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, "Nessun blocco inserito.", new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())

    df = df_blocchi.copy()
    df["Giorno"] = pd.to_datetime(df["Giorno"])
    df = df.sort_values("Giorno")

    for giorno, gruppo in df.groupby("Giorno", sort=True):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(200, 40, 40)
        pdf.cell(0, 10, _pdf_safe(_nome_giorno(giorno)), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

        for _, riga in gruppo.iterrows():
            assegna_a = str(riga.get("Assegna a") or "Tutta la squadra")
            tipo = str(riga.get("Tipo sessione") or "")
            descrizione = str(riga.get("Descrizione") or "")
            target = riga.get("Target")

            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 7, _pdf_safe(f"{assegna_a} - {tipo}"), new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 11)
            testo = descrizione
            if target and str(target).strip():
                testo += f"  (rif: {target})"
            pdf.multi_cell(0, 6, _pdf_safe(testo), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

        pdf.ln(3)

    return bytes(pdf.output())


def genera_pdf_pattern(settimane: list[dict], titolo: str = "Programma") -> bytes:
    """
    settimane: stessa forma di st.session_state["programma_settimane"] — lista
    di {"nome": str, "blocchi": [{"Giorno settimana": ..., "Tipo sessione": ...,
    "Descrizione": ..., "Target": ..., "Assegna a": ...}, ...]}.

    A differenza di genera_pdf_settimana(), raggruppa per nome del giorno
    della settimana (Lunedi..Domenica) invece che per data reale: un pattern
    non ha ancora una data finche' non viene assegnato.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, _pdf_safe(titolo), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    blocchi_totali = sum(len(s.get("blocchi", [])) for s in settimane)
    if not settimane or blocchi_totali == 0:
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(0, 10, "Nessun blocco inserito.", new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())

    for settimana in settimane:
        blocchi = settimana.get("blocchi", [])
        if not blocchi:
            continue

        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 11, _pdf_safe(settimana.get("nome") or "Settimana"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

        blocchi_ordinati = sorted(blocchi, key=lambda b: GIORNI_ORDINE_ACCENTATO.index(b["Giorno settimana"]))
        giorno_corrente = None
        for riga in blocchi_ordinati:
            if riga["Giorno settimana"] != giorno_corrente:
                giorno_corrente = riga["Giorno settimana"]
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(200, 40, 40)
                pdf.cell(0, 10, _pdf_safe(giorno_corrente), new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(0, 0, 0)

            assegna_a = str(riga.get("Assegna a") or "Tutta la squadra")
            tipo = str(riga.get("Tipo sessione") or "")
            descrizione = str(riga.get("Descrizione") or "")
            target = riga.get("Target")

            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 7, _pdf_safe(f"{assegna_a} - {tipo}"), new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 11)
            testo = descrizione
            if target and str(target).strip():
                testo += f"  (rif: {target})"
            pdf.multi_cell(0, 6, _pdf_safe(testo), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

        pdf.ln(4)

    return bytes(pdf.output())
