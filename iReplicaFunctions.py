#
# Script for fetching email attachments from the inbox of a given gmail account
#
# Created by Adam Khoukhi on 08/25/22.

import os
import email
import imaplib
from dotenv import load_dotenv
import csv
import matplotlib
from matplotlib import pyplot as plt
import numpy as np
import math

load_dotenv()
path = os.getcwd()


# Current imap is for Gmail
imap_url = os.getenv('IMAP_URL')
connection = imaplib.IMAP4_SSL(imap_url)

means = []
medians = []
weights = []
alphas = []
onBetas = []
offBetas = []
ISO = []
SS = []


def login():
    """
    Login into a gmail account. Required to run before running @read_inbox
    """
    # Email's Address and Password
    email_address = os.getenv('EMAIL_ADDRESS')
    password = os.getenv('PASSWORD')
    connection.login(email_address, password)


def read_inbox():
    """
        Reads the inbox of the gmail account that was used in the login method
    """
    # login into the account
    login()

    # No need to check spam or trash, only Inbox
    connection.select('Inbox', readonly=True)

    result, msgnums = connection.search(None, 'ALL')
    if result != "OK":
        print("Error in searching inbox")
    else:
        index = 1
        for num in msgnums[0].split():
            typ, raw_data = connection.fetch(num, '(RFC822)')
            if typ.__eq__("OK"):
                raw_email = raw_data[0][1]
                raw_email_string = raw_email.decode('utf-8')
                email_message = email.message_from_string(raw_email_string)

                subject = str(email_message).split("Subject: ", 1)[1].split("\nMessage-Id:", 1)[0]
                if subject.__eq__("iReplica 3.0 Session Data"):
                    for part in email_message.walk():
                        if part.get('Content-Disposition') is None:
                            continue
                        file_name_components = part.get_filename().split('.')
                        file_name = file_name_components[0] + "_" + str(index) + "." + file_name_components[1]
                        if bool(file_name):
                            file_path = os.path.join((path + '/Datasheets/'), file_name)
                            index = index + 1
                            if not os.path.isfile(file_path):
                                fp = open(file_path, 'wb')
                                fp.write(part.get_payload(decode=True))
                                fp.close()
        print('Number of downloads: {}'.format((index - 1)))
        connection.logout()


def clear_datasheets():
    """
        Removes all the files inside the Datasheets directory
    """
    # path of the directory
    # Getting the list of datasheets clearing the directory
    for file in os.listdir((path + '/Datasheets/')):
        os.remove(os.path.join((path + '/Datasheets/'), file))


def calculate_median(arr):
    """
        Calculates the median of a given array
    """
    percentile = 1524096
    currentSum = 0
    median = 0
    index = 0
    for i in arr:
        if currentSum >= percentile:
            return index
        currentSum += int(i)
        index += 1


def calculate_mean(arr):
    """
        Calculates the mean of a given array
    """
    sumOfLuminosities = 0
    sampleSize = 3048192.0
    index = 0
    for i in arr:
        sumOfLuminosities += (index * int(i))
        index += 1
    return sumOfLuminosities / sampleSize


def read_csv():
    """
        Reads the data in all the csv files located in the Datasheets directory
    """

    # Getting the list of datasheets clearing the directory
    for file in os.listdir((path + '/Datasheets/')):
        # open csv file
        with open(os.path.join((path + '/Datasheets/'), file)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if len(row) > 0:
                    if row[0] == 'Weight ':
                        weights.append(float(row[1]))
                    elif row[0] == 'Alpha ':
                        alphas.append(float(row[1]))
                    elif row[0] == 'ON Beta ':
                        onBetas.append(float(row[1]))
                    elif row[0] == 'OFF Beta ':
                        offBetas.append(float(row[1]))
                    elif row[0] == 'ISO (Fastest to slowest) ':
                        ISO.append(float(row[3]))
                    elif row[0] == 'Exposure Time (Fastest to slowest) ':
                        SS.append(float(row[3]))
                    elif row[0] == 'luminosity Histograms 0-16383 ':
                        means.append(calculate_mean(row[1:]))
                        medians.append(calculate_median(row[1:]))

    normalizeMeansAndMedians()


def normalizeMeansAndMedians():
    """
        Normalizes the mean and median by multiplying them with a factor
    """

    for i in range(0, len(means)):
        means[i] = math.log(means[i] * ISO[i] * SS[i])

    for i in range(0, len(medians)):
        medians[i] = math.log((medians[i] * ISO[i] * SS[i]))


def createAndSavePlot(x, y, x_name, y_name):
    """
        Plots and saves the Visualization of the x and y set of values given as a png in the Plots folder
    """
    plt.title(x_name + " vs. " + y_name)
    plt.scatter(x, y, color="blue")
    (slope, intercept) = np.polyfit(x, y, 1)
    plt.plot(np.unique(x), np.poly1d(np.polyfit(x, y, 1))(np.unique(x)), color="red")
    plt.plot(0, 0, '-r', label='y = ' + "{:f}".format(slope) + 'x + ' + str(intercept))
    plt.plot(0, 0, '-b', label='r = ' + "{:f}".format(np.corrcoef(x, y)[0][1]))
    plt.legend(loc='upper right')
    plt.savefig('./Plots/' + x_name + '_' + y_name + '.png')
    plt.close()


def visualizeData():
    """
        Visualizes the different relations between the different variables
    """
    matplotlib.get_backend()
    matplotlib.use('MacOSX')

    # Median and Weight
    createAndSavePlot(medians, weights, "median", "weight")
    createAndSavePlot(means, weights, "mean", "weight")
    createAndSavePlot(medians, alphas, "median", "alpha")
    createAndSavePlot(means, alphas, "mean", "alpha")
    createAndSavePlot(alphas, weights, "alpha", "weight")
    createAndSavePlot(weights, onBetas, "weight", "nON")
    createAndSavePlot(weights, offBetas, "weight", "nOFF")
    createAndSavePlot(alphas, onBetas, "alpha", "nON")
    createAndSavePlot(alphas, offBetas, "alpha", "nOFF")
    createAndSavePlot(medians, onBetas, "median", "nON")
    createAndSavePlot(medians, offBetas, "median", "nOFF")
    createAndSavePlot(means, onBetas, "mean", "nON")
    createAndSavePlot(means, offBetas, "mean", "nOFF")
    # print(sum(onBetas)/len(onBetas))
    # print(sum(offBetas) / len(offBetas))