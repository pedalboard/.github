#!/usr/bin/python3

import pandas as pd
import argparse


def conversion(text):
    if isinstance(text, str):
        if text.startswith("https://www.digikey.ch/"):
            parts = text.split("/")
            return parts[len(parts) - 2]
    else:
        return text


# Instantiate the parser
parser = argparse.ArgumentParser(description="bon2inventree.py")

# Required positional argument
parser.add_argument("input_file", type=str, help="input file")
parser.add_argument("output_file", type=str, help="output file")

args = parser.parse_args()

file_path = args.input_file
column_name = "Supplier"
df = pd.read_csv(file_path)
df[column_name] = df[column_name].map(conversion)
df.to_csv(args.output_file)
