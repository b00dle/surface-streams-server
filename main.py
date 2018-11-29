import connexion
from flask import render_template

# Create the application instance
app = connexion.App(__name__, specification_dir='./')
# Read the swagger.yml file to configure the endpoints
app.add_api('swagger.yml')


# Create a URL route in our application for "/"
@app.route('/')
def home():
    """
    This function just responds to the browser URL
    localhost:5000/
    :return:        the rendered template 'home.html'
    """
    return render_template('home.html')


def server_main():
    # app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    app.run(host='0.0.0.0', port=5000)


def plotting_main():
    from plotting import stats_plotter
    stats_plotter.plot_monitor_stats([
        "measurements/mp4-480-320.txt",
        "measurements/mp4-640-480.txt",
        "measurements/mp4-1280-960.txt"
    ])


# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    server_main()
    #plotting_main()