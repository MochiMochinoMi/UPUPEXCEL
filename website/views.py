from flask import Blueprint, render_template, request, session, redirect, url_for
import os
from .logic import extract_zip,plot_stock_data,plot_single_daily_data
import glob
from flask import render_template, request, session, redirect, url_for
import time
from flask import redirect, url_for



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
                plot_stock_data(folder_path, start_date, end_date, duration, stock_names, plot_variable=variable, log_scale=log_scale)
                plot_file_name = 'GRAPH.png'
                plot_file_path = os.path.join(plot_file_name)
                return redirect(url_for('views.show_graph', plot_path=plot_file_path))
            
        elif plot_type == 'plot_daily_change':
            log_scale = False  # Default value
            folder_path = session.get('folder_path')
            time = request.form['fixed_date']
            ticker = request.form['ticker']
            log_scale = 'log_scale' in request.form
            plot_single_daily_data(folder_path, ticker, time, log_scale=False)
            plot_file_name = 'GRAPH2.png'
            plot_file_path = plot_file_name
            return redirect(url_for('views.show_graph', plot_path=plot_file_path))
    delete_cached_images()
    return render_template('graph_selection.html')








@views.route('/show_graph')
def show_graph():
    plot_file_path = request.args.get('plot_path')
    time.sleep(5)
    return render_template('show_graph.html', plot_path=plot_file_path)


def delete_cached_images():
    static_folder = os.path.join(os.getcwd(),"website" ,'static')
    cached_images = glob.glob(os.path.join(static_folder, 'GRAPH*.png'))
    for image_path in cached_images:
        os.remove(image_path)
