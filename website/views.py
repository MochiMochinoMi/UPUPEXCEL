from flask import Blueprint, render_template, request, send_file, session, redirect, url_for,send_from_directory,flash
import pandas as pd
import os
from .logic import extract_zip, stack_excel_data, plot_stock_data,plot_single_daily_data,is_valid_date,Wplot_stock_data,Wplot_single_daily_data
import matplotlib.pyplot as plt
import threading
import glob
from flask import render_template, request, send_file, session, redirect, url_for, send_from_directory, flash, make_response
import time
from flask import redirect, url_for
from datetime import datetime
import xlrd


views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":
        uploaded_file = request.files['file']
        file_path = "uploaded_file.zip"
        uploaded_file.save(file_path)
        # Extract the ZIP file
        extracted_folder = extract_zip(file_path)
        # Construct the full folder path
        folder_path = os.path.join(extracted_folder)
        session['folder_path'] = folder_path
        print("Folder Path:", folder_path)
        return redirect(url_for('views.graph_selection'))

    return render_template('base.html')

def plot_graph(folder_path, start_date, end_date, duration, stock_names,variable,log_scale):

    data = stack_excel_data(folder_path)
    data.index = data.index.date

    plot_stock_data(data, start_date, end_date, duration, stock_names,variable,log_scale)

    # Set a session variable with the warning message

def plot_graph2(folder_path, fixed_date, ticker,log_scale):

    # Process the fixed_date input as a datetime object
    time= datetime.strptime(fixed_date, "%Y-%m-%d").date()
    data = stack_excel_data(folder_path)
    data.index = data.index.date

    plot_single_daily_data(data, ticker, time,log_scale)







@views.route('/graph_selection', methods=['GET', 'POST'])
def graph_selection():

    if request.method == 'POST':
        
        plot_type = request.form['plot_type']
        if plot_type == 'plot_any_stock':
                log_scale = False  # Default value
                folder_path = session.get('folder_path')
                start_date = request.form['start_date']
                end_date = request.form['end_date']
                duration = request.form['duration']
                stock_names = request.form['stock_names']
                stock_names = [name.strip() for name in stock_names.split(',')]
                variable = request.form['variable']
                log_scale = 'log_scale' in request.form
                # Check if form data is valid
                if not is_valid_date(start_date) or not is_valid_date(end_date):
                    flash('Please enter a valid date in the format YYYY-MM-DD.')
                    return render_template('graph_selection.html')
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                graph_thread = threading.Thread(target=plot_graph, args=(session.get('folder_path'), start_date, end_date, duration, stock_names,variable,log_scale))
                graph_thread.start()
                plot_file_name = 'stock_data_plot.jpg'
                plot_file_path = os.path.join('website', 'static', plot_file_name)
                return redirect(url_for('views.show_graph', plot_path=plot_file_path))
            
        elif plot_type == 'plot_daily_change':
            log_scale = False  # Default value
            folder_path = session.get('folder_path')
            time = request.form['fixed_date']
            ticker = request.form['ticker']
            log_scale = 'log_scale' in request.form
            if not is_valid_date(time):
                flash('Please enter a valid date in the format YYYY-MM-DD.')
                return render_template('graph_selection.html')
            time= datetime.strptime(time, "%Y-%m-%d").date()
            graph_thread = threading.Thread(target=plot_graph2, args=(session.get('folder_path'), time, ticker,log_scale))
            graph_thread.start()
            plot_file_name = 'stock_data_plot_daily.jpg'
            plot_file_path = os.path.join('website', 'static', plot_file_name)
            return redirect(url_for('views.show_graph', plot_path=plot_file_path))

    delete_cached_images()
    return render_template('graph_selection.html')




@views.route('/show_graph')
def show_graph():
    plot_file_path = request.args.get('plot_path')

    # Delay for 1 second to allow time for the image to be generated
    time.sleep(25)
    # Render the show_graph.html template with the plot_path variable

    return render_template('show_graph.html', plot_path=plot_file_path)


def delete_cached_images():
    static_folder = os.path.join(os.getcwd(), 'website', 'static')
    cached_images = glob.glob(os.path.join(static_folder, 'stock_data_plot*.jpg'))
    for image_path in cached_images:
        os.remove(image_path)
