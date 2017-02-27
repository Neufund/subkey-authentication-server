#!/usr/bin/env python
import argparse

import db

parser = argparse.ArgumentParser(description='Load data from fixture to DB')
parser.add_argument('-f', '--fixture', metavar='F', type=str, help='Fixture to load')
parser.add_argument('-db', '--database_name', metavar='DB', type=str, help='DB name')

args = parser.parse_args()

db.load_fixture(args.fixture, args.database_name)
