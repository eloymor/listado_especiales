from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import CSVFileUploadForm, LoginForm
from .models import CSVData, Report
from .helper import convert_date_format, costumers_delay
from datetime import date, datetime
import pandas as pd
import json
from plotly.utils import PlotlyJSONEncoder
import plotly.express as px
import os
import threading
import time


def delete_objects_later(minutes=5):
    """
    Deletes objects from models after 5 minutes (300 seconds).
    """
    seconds = minutes * 60
    time.sleep(seconds)
    CSVData.objects.all().delete()
    Report.objects.all().delete()


@login_required(login_url='llistat:login')
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
                    with open(csv_path, 'r') as f:
                        first_line = f.readline()
                        if ";" in first_line:
                            delimiter = ";"
                        else:
                            delimiter = ","
                        f.seek(0)

                    df = pd.read_csv(csv_path, delimiter=delimiter)

                    # Modify columns names
                    df.rename(columns={
                        "Fecha Creación": "Fecha_Creacion",
                        "Fecha Cierre": "Fecha_Cierre",
                        "Fecha Fin Prevista": "Fecha_Fin_Prevista"
                    }, inplace=True)

                    df = df.replace({float('nan'): None}) # np.nan to None for Django ORM
                    if "Cerrado" in df.columns:
                        df["Cerrado"] = df["Cerrado"].apply(
                            lambda x: True if str(x).strip().lower() == "true" else False if str(x).strip().lower()\
                                == "false" else None
                        )
                    if "PCP Lock" in df.columns:
                        df["PCP Lock_bit"] = df["PCP Lock_bit"].apply(
                        lambda x: True if str(x).strip().lower() == "true" else False if str(x).strip().lower()\
                            == "false" else None
                        )

                    if "Usuario" in df.columns:
                        df = df.drop(columns=["Usuario"])

                except Exception as e:
                    if os.path.exists(csv_path):
                        os.remove(csv_path)
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
                    if os.path.exists(csv_path):
                        os.remove(csv_path)
                    return render(request, 'llistat/upload.html', {
                        'form': form,
                        'error': f"Error saving CSV data to database: {e}"
                    })


                return redirect('llistat:report')

        else:
            return render(request, 'llistat/upload.html', {
                'form': form,
                'error': f"Only .csv files are supported."
            })

    else:
        form = CSVFileUploadForm()

    return render(request, 'llistat/upload.html', {'form': form})



@login_required(login_url='llistat:login')
def report(request):

    queryset = CSVData.objects.all()
    if queryset.count() == 0:
        return redirect('llistat:upload_csv')
    else:
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
            item.is_delay = (item.FECHA_ENTREGA and item.FECHA_ENTREGA < date.today())

        thread = threading.Thread(target=delete_objects_later)
        thread.start()

        return render(request, 'llistat/report.html', {'report': report})


def user_login(request):
    error_message = None
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request,
                         username=form.cleaned_data['username'],
                         password=form.cleaned_data['password'])
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                error_message = "Usuario o contraseña incorrecto"
                # return HttpResponse("error - invalid credentials")
    else:
        form = LoginForm(request.POST or None)
    return render(request,
                  'llistat/login.html',
                  {'form': form,
                   'error_message': error_message})
@login_required(login_url='llistat:login')
def plot_report(request):

    queryset = Report.objects.all()
    if queryset.count() == 0:
        return redirect('llistat:upload_csv')
    else:
        report = Report.objects.all()
        data = list(report.values())
        df = pd.DataFrame(data)
        df['Fecha_Fin_Prevista'] = pd.to_datetime(df['Fecha_Fin_Prevista'], yearfirst=True)

        fig1 = px.pie(df['Seccion'].value_counts(),
                     values='count',
                     names=df['Seccion'].value_counts().index,
                     template="plotly_white",
                     height=400, width=400,
                     title="% Secciones por tarea total")
        fig_json_1 = json.dumps(fig1, cls=PlotlyJSONEncoder)

        report_pet, report_pet_delay = costumers_delay(df)
        stacked_data = pd.DataFrame({
            "Peticionarios": report_pet.index,  # x-axis
            "En curso": report_pet['count'],  # First series
            "Retrasada": report_pet_delay['count']  # Second series
        })
        stacked_data['Peticionarios'] = stacked_data.index  # Correct column values to match original index

        fig2 = px.bar(
            stacked_data.sort_values(by='En curso', ascending=False),
            x="Peticionarios",  # x-axis
            y=["En curso", "Retrasada"],  # Stack these series
            labels={
                "Peticionarios": "Peticionarios",  # x-axis label
                "value": "Total tareas",  # y-axis label
                "variable": "Estado tarea"  # Label for legend
            },
            template="plotly_white",
            height=400,
            width=750,
            title="Top 10 Peticionarios"
        )
        fig_json_2 = json.dumps(fig2, cls=PlotlyJSONEncoder)

        today = datetime.today()
        report_delay_seccion = df.loc[(df['Fecha_Fin_Prevista'] < today)]['Seccion'].value_counts()

        fig3 = px.pie(report_delay_seccion,
                     values='count',
                     names=report_delay_seccion.index,
                     template="plotly_white",
                     height=400, width=400,
                     title='% Sección por tareas en atraso')

        fig_json_3 = json.dumps(fig3, cls=PlotlyJSONEncoder)

        df['delay'] = df['Fecha_Fin_Prevista'].apply(lambda x: 'Atraso' if x < today else 'En curso')
        agg_data = df.groupby(['Seccion', 'delay']).size().reset_index(name='count')

        fig4 = px.sunburst(data_frame=agg_data,
                           values='count',
                           path=['Seccion', 'delay'],
                           color='delay',
                           color_discrete_map={'Atraso': 'red', 'En curso': 'green', 'MRP': 'blue', 'OT': 'orange'},
                           template="plotly_white",
                           height=400, width=750,
                           title="Tareas por sección y estado")

        fig_json_4 = json.dumps(fig4, cls=PlotlyJSONEncoder)

        return render(request, 'llistat/plots.html', {'fig_json_1': fig_json_1,
                                                                         'fig_json_2': fig_json_2,
                                                                         'fig_json_3': fig_json_3,
                                                                         'fig_json_4': fig_json_4})
