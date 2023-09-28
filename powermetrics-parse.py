#!./bin/python3
import os
import re
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
#import configparser
import json
import argparse





def regexParse(content, testName, config):
    # Declare local dataframes
    dfPower, dfFrequency, dfUsage = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Regex findall returns matches which are all strings
    # Used list(map(int, regexMatches))) to convert the list of strings to a list of int or float so that in Excel it's an integer
    #dfPower['Efficiency Cluster'] = pd.Series(map(int, re.findall(r'E-Cluster Power:\s*([\d.]+)\s*mW', content)))

    powMeasure = config["Measures"]["power"]
    if powMeasure["enable"]:
        for device in powMeasure["devices"]:
            for nr in range(0, len(device["regexps"])):
                if len(device["regexps"]) == 1:
                    name = device["name"]
                else:
                    name = device["name"] + str(nr)
                regexp = device["regexps"][nr]
                dfPower[name] = pd.Series(map(int, re.findall(regexp, content)))

    freqMeasure = config["Measures"]["frequency"]
    if freqMeasure["enable"]:
        for device in freqMeasure["devices"]:
            for nr in range(0, len(device["regexps"])):
                if len(device["regexps"]) == 1:
                    name = device["name"]
                else:
                    name = device["name"] + str(nr)
                regexp = device["regexps"][nr]
                dfFrequency[name] = pd.Series(map(int, re.findall(regexp, content)))

    usageMeasure = config["Measures"]["usage"]
    if usageMeasure["enable"]:
        for device in usageMeasure["devices"]:
            for nr in range(0, len(device["regexps"])):
                if len(device["regexps"]) == 1:
                    name = device["name"]
                else:
                    name = device["name"] + str(nr)
                regexp = device["regexps"][nr]
                dfUsage[name] = pd.Series(map(float, re.findall(regexp, content)))


     # Check if the number of data-points from all tests are equal
    if(len(dfPower) != len(dfFrequency) or len(dfUsage) != len(dfFrequency)):
        print("The lengths of the dataframes are not equal. Check the regexes.") 
    else:
        dataPoints = len(dfPower)
        dfPower['time'] = dfFrequency['time'] = dfUsage['time'] = list(range(1, dataPoints + 1))
        dfPower['Test Name'] = dfFrequency['Test Name'] = dfUsage['Test Name'] = [testName] * dataPoints


    return dfPower, dfFrequency, dfUsage    


def buildCharts(dfPower, dfFrequency, dfUsage, config, outDir):

    # Common Plotly config parameter to be passed to each chart
    configPlt = dict({
        'modeBarButtonsToRemove': ['toggleSpikelines', 'hoverClosestCartesian',  'hoverCompareCartesian', 'select2d', 'lasso2d'],
        'displaylogo': False
    })

    label_tests = dfFrequency["Test Name"].value_counts().index # get the labels of the tests

    # POWER

    if config["Measures"]["power"]["enable"]:

        colorMap = dict()
        for device in config["Measures"]["power"]["devices"]:
            for nr in range(0, len(device["colors"])):
                if len(device["colors"]) == 1:
                    name = device["name"]
                else:
                    name = device["name"] + str(nr)
                colorMap[name] = device["colors"][nr]

        # Figure for Package Power Over Time
        fig = px.area(dfPower.loc[dfPower["Test Name"].isin(label_tests)], x='time', y=dfPower.columns[:len(dfPower.columns)-2], template='plotly_dark', 
        line_shape= "linear", facet_row = 'Test Name',
            labels={"value": "Power Consumption (mW)", "time": "Time (s)"}, color_discrete_map=colorMap,
            category_orders={"Test Name": label_tests}
        )    
        
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        for annotation in fig['layout']['annotations']:
            annotation['font'] = dict(family="SF Pro Display, Roboto, Droid Sans, Arial", size=11)
        
        fig.update_yaxes(type='linear', title_font = dict(size=12), color="#707070", title_font_color = "#707070", tickfont = dict(size = 9), gridcolor='#242424', zerolinecolor = '#242424')
        fig.update_xaxes(showgrid=False, title_font = dict(size=10), color="#707070", title_font_color = "#707070", tickfont = dict(size = 9))
        fig.update_traces(hovertemplate='%{y} (mW)', line=dict(width=1.0))
        fig.update_layout(autosize = True, hovermode="x", 
            showlegend = True, font = dict(family="SF Pro Display, Roboto, Droid Sans, Arial"),
            title={
                'text': "<b>Package Power Consumption over Time</b> <br> <sup> " + config["Test"].get("title").replace("\"","") + " | " +  config["Test"].get("soc").replace("\"","") + " | " + config["Test"].get("os").replace("\"","") + " </sup>",
                'y':0.92,
                'x':0.54,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18, color='#FFF')},
            margin = dict(r = 50, t = 80),
            margin_pad = 10,
            modebar = dict(orientation = 'v'),
            plot_bgcolor='#191C1F',
            paper_bgcolor ='#191C1F'
        )

        fig.write_image(os.path.join(outDir, "power-package.svg"))


        # BAR CHART FOR Averages by component
        barDf = (dfPower.loc[dfPower["Test Name"].isin(label_tests)]).groupby(['Test Name']).mean().reset_index()
        fig = px.bar(barDf, x='Test Name', y=dfPower.columns[:len(dfPower.columns)-2], template='plotly_dark', orientation='v', hover_name = 'Test Name',
        barmode = 'group',
        color_discrete_map=colorMap,
        labels={"value": "Power (mW)"}, 
        category_orders={"Test Name": label_tests})

        fig.update_yaxes(title_font = dict(size=12), color="#707070", title_font_color = "#707070", tickfont = dict(size = 9), gridcolor='#242424', zerolinecolor = '#242424')
        fig.update_xaxes(zeroline = True, showgrid=False, color="#FFF", title_font_color = "#707070", tickfont = dict(size = 11), title_text='')
        fig.update_traces(hovertemplate='%{y:.0f} ()', texttemplate='%{y:.0f} mW', textfont= dict(size=8), width=[0.15, 0.15, 0.15, 0.15, 0.15])
        fig.update_layout( autosize = True, hovermode=False, legend_title_text='',
            legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="center", x=0.5), 
            font = dict(family="SF Pro Display, Roboto, Droid Sans, Arial"),
            title={
                'text': "<b>Average Power Consumption</b> <br> <sup> " + config["Test"].get("title").replace("\"","") + " | " +  config["Test"].get("soc").replace("\"","") + " | " + config["Test"].get("os").replace("\"","") + " </sup>",
                'y':0.92,
                'x':0.54,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18, color='#FFF')},
            margin = dict(r = 30, b = 0, t = 80),
            margin_pad = 10,
            modebar = dict(orientation = 'v'),
            plot_bgcolor='#191C1F',
            paper_bgcolor ='#191C1F'
        )

        fig.write_image(os.path.join(outDir, "power-package-average.svg"))


    # FREQUENCY

    if config["Measures"]["frequency"]["enable"]:

        colorMap = dict()
        for device in config["Measures"]["frequency"]["devices"]:
            for nr in range(0, len(device["colors"])):
                if len(device["colors"]) == 1:
                    name = device["name"]
                else:
                    name = device["name"] + str(nr)
                colorMap[name] = device["colors"][nr]

        # Figure for CPU, GPU Frequency over time
        fig = px.line(dfFrequency.loc[dfFrequency["Test Name"].isin(label_tests)], x='time', y=dfFrequency.columns[:len(dfFrequency.columns)-2], template='plotly_dark', 
    facet_row='Test Name', line_shape= "linear", render_mode = "svg",  facet_col_wrap = 5,
        color_discrete_map=colorMap,
        labels={"value": "Frequency (MHz)", "time": "Time (s)"},
        category_orders={"Test Name": label_tests}
        )
        
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        for annotation in fig['layout']['annotations']:
            annotation['font'] = dict(family="SF Pro Display, Roboto, Droid Sans, Arial", size=11)
        
        fig.update_yaxes(type='linear', title_font = dict(size=12), color="#707070", title_font_color = "#707070", tickfont = dict(size = 9), gridcolor='#242424', zerolinecolor = '#242424')
        fig.update_xaxes(showgrid=False, title_font = dict(size=10), color="#707070", title_font_color = "#707070", tickfont = dict(size = 9))
        fig.update_traces(hovertemplate='%{y} MHz', line=dict(width=1.0))
        fig.update_layout(legend_title_text='', autosize = True, hovermode="x", 
            legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5), 
            font = dict(family="SF Pro Display, Roboto, Droid Sans, Arial"),
            title={
                'text': "<b>Frequency over Time</b> <br> <sup> " + config["Test"].get("title").replace("\"","") + " | " +  config["Test"].get("soc").replace("\"","") + " | " + config["Test"].get("os").replace("\"","") + " </sup>",
                'y':0.92,
                'x':0.54,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18, color='#FFF')},
            margin = dict(r = 50, t = 80),
            margin_pad = 10,
            modebar = dict(orientation = 'v'),
            plot_bgcolor='#191C1F',
            paper_bgcolor ='#191C1F'
        )

        fig.write_image(os.path.join(outDir, "frequency.svg"))

        # Average Frequency
        barDf = (dfFrequency.loc[dfFrequency["Test Name"].isin(label_tests)]).groupby(['Test Name']).mean().reset_index()
        fig = px.bar(barDf, x='Test Name', y=dfFrequency.columns[:len(dfFrequency.columns)-2], template='plotly_dark', orientation='v', hover_name = 'Test Name',
        barmode = 'group', 

        color_discrete_map=colorMap,
        labels={"value": "Frequency (MHz)"}, 
        category_orders={"Test Name": label_tests})

        fig.update_yaxes(title_font = dict(size=12), color="#707070", title_font_color = "#707070", tickfont = dict(size = 9), gridcolor='#242424', zerolinecolor = '#242424')
        fig.update_xaxes(zeroline = True, showgrid=False, color="#FFF", title_font_color = "#707070", tickfont = dict(size = 11), title_text='')
        fig.update_traces(hovertemplate='%{y:.0f} (Hz)', texttemplate='%{y:.0f}', textfont= dict(size=8), width=[0.15, 0.15, 0.15, 0.15, 0.15])
        fig.update_layout( autosize = True, hovermode=False, legend_title_text='',
            legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="center", x=0.5), 
            font = dict(family="SF Pro Display, Roboto, Droid Sans, Arial"),
            title={
                'text': "<b>Average Frequency</b> <br> <sup> " + config["Test"].get("title").replace("\"","") + " | " +  config["Test"].get("soc").replace("\"","") + " | " + config["Test"].get("os").replace("\"","") + " </sup>",
                'y':0.92,
                'x':0.54,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18, color='#FFF')},
            margin = dict(r = 30, b = 0, t = 80),
            margin_pad = 10,
            modebar = dict(orientation = 'v'),
            plot_bgcolor='#191C1F',
            paper_bgcolor ='#191C1F'
        )

        fig.write_image(os.path.join(outDir, "frequency-average.svg"))


    # USAGE

    if config["Measures"]["usage"]["enable"]:

        colorMap = dict()
        for device in config["Measures"]["usage"]["devices"]:
            for nr in range(0, len(device["colors"])):
                if len(device["colors"]) == 1:
                    name = device["name"]
                else:
                    name = device["name"] + str(nr)
                colorMap[name] = device["colors"][nr]

        # Figure for CPU, GPU Usage over time
        fig = px.line(dfUsage.loc[dfUsage["Test Name"].isin(label_tests)], x='time', y=dfUsage.columns[:len(dfUsage.columns)-2], template='plotly_dark', 
        facet_row='Test Name', line_shape= "linear", render_mode = "svg",  facet_col_wrap = 5,

        color_discrete_map=colorMap,
        labels={"value": "Usage (%)", "time": "Time (s)"},
        category_orders={"Test Name": label_tests})
        
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        for annotation in fig['layout']['annotations']:
            annotation['font'] = dict(family="SF Pro Display, Roboto, Droid Sans, Arial", size=11)
        
        fig.update_yaxes(type='linear', title_font = dict(size=12), color="#707070", title_font_color = "#707070", tickfont = dict(size = 9), gridcolor='#242424', zerolinecolor = '#242424', ticksuffix = "%")
        fig.update_xaxes(showgrid=False, title_font = dict(size=10), color="#707070", title_font_color = "#707070", tickfont = dict(size = 9))
        fig.update_traces(hovertemplate='%{y:.0f} %', line=dict(width=1.0))
        fig.update_layout(legend_title_text='', autosize = True, hovermode="x", 
            legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5), 
            font = dict(family="SF Pro Display, Roboto, Droid Sans, Arial"),
            title={
                'text': "<b>Usage over Time</b> <br> <sup> " + config["Test"].get("title").replace("\"","") + " | " +  config["Test"].get("soc").replace("\"","") + " | " + config["Test"].get("os").replace("\"","") + " </sup>",
                'y':0.92,
                'x':0.54,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18, color='#FFF')},
            margin = dict(r = 50, t = 80),
            margin_pad = 10,
            modebar = dict(orientation = 'v'),
            plot_bgcolor='#191C1F',
            paper_bgcolor ='#191C1F'
        )


        fig.write_image(os.path.join(outDir, "usage.svg"))

        # BAR CHART FOR Averages by component
        barDf = (dfUsage.loc[dfUsage["Test Name"].isin(label_tests)]).groupby(['Test Name']).mean().reset_index()
        fig = px.bar(barDf, x='Test Name', y=dfUsage.columns[:len(dfUsage.columns)-2], template='plotly_dark', orientation='v', hover_name = 'Test Name',
        barmode = 'group',
        color_discrete_map=colorMap,
        labels={"value": "Usage (%)"}, 
        category_orders={"Test Name": label_tests})

        fig.update_yaxes(title_font = dict(size=12), color="#707070", title_font_color = "#707070", tickfont = dict(size = 9), gridcolor='#242424', zerolinecolor = '#242424', ticksuffix = "%")
        fig.update_xaxes(zeroline = True, showgrid=False, color="#FFF", title_font_color = "#707070", tickfont = dict(size = 11), title_text='')
        fig.update_traces(hovertemplate='%{y:.0f} (%)', texttemplate='%{y:.0f} %', textfont= dict(size=8), width=[0.15, 0.15, 0.15, 0.15, 0.15])
        fig.update_layout( autosize = True, hovermode=False, legend_title_text='',
            legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="center", x=0.5), 
            font = dict(family="SF Pro Display, Roboto, Droid Sans, Arial"),
            title={
                'text': "<b>Average Usage</b> <br> <sup> " + config["Test"].get("title").replace("\"","") + " | " +  config["Test"].get("soc").replace("\"","") + " | " + config["Test"].get("os").replace("\"","") + " </sup>",
                'y':0.92,
                'x':0.54,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=18, color='#FFF')},
            margin = dict(r = 30, b = 0, t = 80),
            margin_pad = 10,
            modebar = dict(orientation = 'v'),
            plot_bgcolor='#191C1F',
            paper_bgcolor ='#191C1F'
        )

        fig.write_image(os.path.join(outDir, "usage-average.svg"))


def main():

    # Parse arguments
    parser = argparse.ArgumentParser( description="Parse powermetrics logs and generate charts" )
    parser.add_argument("config", help=".json file containing the configuration")
    parser.add_argument("out", help="output directory")
    args = parser.parse_args()
    if(not os.path.isfile(args.config)):
        print(args.config + " is not a file")
        exit(-1)
    if(not os.path.isdir(args.out)):
        answer = ""
        while(answer != "y" and answer != "n"):
            answer = input(args.out + " is not a a directory, do you want to create it? (y/n) ").lower()
        if answer == "y":
            os.makedirs(args.out)
        else:
            exit(0)

    # Parse config file    
    with open(args.config, 'r') as file:
        config = json.load(file)
    if not "Id" in config or config["Id"] != "powermetrics":
        print(args.config + " is not a proper config file")
        exit(-1)
    


    start_time = time.time()
    print("Starting at = ", time.ctime(start_time))
    directory_path = os.getcwd()

    # Current directory should have a folder named powermetric-logs which contains the output logs of powermetric runs
    powerLogsFolderName = "powermetric-logs"

    # Build the full path to the logs folder
    pathLogsFolder = directory_path + '/' + powerLogsFolderName + '/'

    # Get the list of all log files in the logs folder
    powerLogsList = os.listdir(pathLogsFolder)

    # Create local dataframes
    dfPower, dfFrequency, dfUsage = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()    

    # Parse each log file
    for logsFile in powerLogsList:

        if not os.path.isfile(pathLogsFolder + logsFile): 
            print('File does not exist.')
        else:
            file = open(pathLogsFolder + logsFile, 'r', encoding="utf8", errors='ignore')
            content = file.read()
        
        # Used to name the test from file paths like TESTXXXX.txt
        testName = os.path.splitext(logsFile)[0]

        # Parse the content and build Data Frames
        dfPowerTemp, dfFrequencyTemp, dfUsageTemp = regexParse(content, testName, config)        
        dfPower     = pd.concat([dfPower, dfPowerTemp], ignore_index=True)
        dfFrequency = pd.concat([dfFrequency, dfFrequencyTemp], ignore_index=True)
        dfUsage     = pd.concat([dfUsage, dfUsageTemp], ignore_index=True)


    # Build charts and output the Excel file
    buildCharts(dfPower, dfFrequency, dfUsage, config, args.out)    

    #print(dfPower)
    end_time = time.time()
    print("Ending at = ", time.ctime(end_time))
    print(f"It took {end_time-start_time:.2f} Time (s) to compute")


if __name__ == "__main__":
    main()