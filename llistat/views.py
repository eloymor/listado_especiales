from django.shortcuts import render, redirect
from .forms import CSVFileUploadForm
from .models import CSVData, Report
from .helper import convert_date_format
from datetime import date
import pandas as pd
import os


def upload_csv(request):
    df = None  # Initialize DataFrame variable
    if request.method == 'POST':
        form = CSVFileUploadForm(request.POST, request.FILES)
        uploaded_file = request.FILES.get('file', None)
        if uploaded_file and uploaded_file.name.endswith('.csv'):
            if form.is_valid():
                # Save the file
                csv_file = form.save()
                csv_path = csv_file.file.path  # Get the file path

                # Load the file content into pandas DataFrame
                try:
                    df = pd.read_csv(csv_path, delimiter=';')
                    # Modify columns names
                    df.rename(columns={
                        "Fecha Creación": "Fecha_Creacion",
                        "Fecha Cierre": "Fecha_Cierre",
                        "Fecha Fin Prevista": "Fecha_Fin_Prevista"
                    }, inplace=True)

                    df = df.replace({float('nan'): None}) # np.nan to None for Django ORM
                    df["Cerrado"] = df["Cerrado"].map({"VERDADERO": True, "FALSO": False})
                    df["PCP Lock_bit"] = df["PCP Lock_bit"].map({"VERDADERO": True, "FALSO": False})

                except Exception as e:
                    return render(request, 'llistat/upload.html', {
                        'form': form,
                        'error': f"Error reading CSV file: {e}"
                    })

                try:

                    CSVData.objects.all().delete()

                    date_fields = ["Fecha_Creacion", "Plazo", "Fecha_Cierre", "FECHA_I",
                                   "Fecha_Fin_Prevista", "FECHA_F", "Fecha_Cliente",
                                   "FECHA_ENTREGA", "FECHA_PREVISTA_MRP"]

                    for date_field in date_fields:
                        df[date_field] = df[date_field].apply(
                            lambda x: convert_date_format(x) if pd.notnull(x) else None
                        )

                    records = [
                        CSVData(
                            Proyecto = row["Proyecto"],
                            OM = row["OM"],
                            Fecha_Creacion = row["Fecha_Creacion"],
                            Peticionario = row["Peticionario"],
                            Factibilidad = row["Factibilidad"],
                            Plazo = row["Plazo"],
                            Cerrado = row["Cerrado"],
                            Fecha_Cierre = row["Fecha_Cierre"],
                            Tarea = row["Tarea"],
                            Usuario = row["Usuario"],
                            FECHA_I = row["FECHA_I"],
                            Fecha_Fin_Prevista = row["Fecha_Fin_Prevista"],
                            FECHA_F = row["FECHA_F"],
                            PCP_Lock_bit = row["PCP Lock_bit"],
                            PCP_Lock = row["PCP Lock"],
                            Unlocking_Remarks = row["Unlocking Remarks"],
                            NUM_PEDIDO = row["NUM_PEDIDO"],
                            Fecha_Cliente = row["Fecha_Cliente"],
                            FECHA_ENTREGA = row["FECHA_ENTREGA"],
                            ESTADO = row["ESTADO"],
                            PROG_MRP = row["PROG_MRP"],
                            QUANTITY = row["QUANTITY"],
                            Seccion = row["Seccion"],
                            FECHA_PREVISTA_MRP = row["FECHA_PREVISTA_MRP"],
                            ProjectDescription = row["ProjectDescription"]
                        )
                        for _, row in df.iterrows()
                    ]
                    CSVData.objects.bulk_create(records)

                    if os.path.exists(csv_path):
                        os.remove(csv_path)

                except Exception as e:
                    return render(request, 'llistat/upload.html', {
                        'form': form,
                        'error': f"Error saving CSV data to database: {e}"
                    })

                # Display the first 5 rows in the template
                # df_html = df.head().to_html()  # Render as HTML table
                # return render(request, 'llistat/upload.html', {
                #     'form': form,
                #     'dataframe': df_html
                # })
                return redirect('llistat:report')

        else:
            return render(request, 'llistat/upload.html', {
                'form': form,
                'error': f"Only .csv files are supported."
            })

    else:
        form = CSVFileUploadForm()

    return render(request, 'llistat/upload.html', {'form': form})


def report(request):

    Report.objects.all().delete()

    OT_sections = ["Mechanical Design", "New solutions"]
    MRP_sections = ["Purchasing"]
    hide_costumers = ["TECNOC"]

    queryset = CSVData.without_F.all()
    data = list(queryset.values())
    df = pd.DataFrame(data)

    df = df.loc[~df["Peticionario"].isin(hide_costumers)] # Hide not used costumers
    OT_OMs_series = df.loc[df["Seccion"].isin(OT_sections), "OM"] # Filter OMs with section OT
    df_final = df.loc[df["Seccion"].isin(MRP_sections), ["Fecha_Fin_Prevista", "OM", "Peticionario", "FECHA_ENTREGA",
                                                         "FECHA_PREVISTA_MRP"]]

    def check_OMs(OM: pd.Series) -> str:
        if OM in OT_OMs_series.values:
            return "OT"
        else:
            return "MRP"

    df_final["Seccion"] = df_final["OM"].apply(check_OMs)
    df_final.sort_values(by=["Fecha_Fin_Prevista", "FECHA_ENTREGA"], inplace=True)

    records = [
        Report(
            Fecha_Fin_Prevista = row["Fecha_Fin_Prevista"],
            OM = row["OM"],
            Peticionario = row["Peticionario"],
            FECHA_ENTREGA = row["FECHA_ENTREGA"],
            FECHA_PREVISTA_MRP = row["FECHA_PREVISTA_MRP"],
            Seccion = row["Seccion"]
        )
        for _, row in df_final.iterrows()
    ]
    Report.objects.bulk_create(records)

    report = Report.objects.all()
    for item in report:
        item.is_past_date = (item.Fecha_Fin_Prevista and item.Fecha_Fin_Prevista < date.today())
    return render(request, 'llistat/report.html', {'report': report})



