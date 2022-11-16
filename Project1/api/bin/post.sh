#!/bin/sh

http --verbose POST localhost:5000/users/ @"$1"
