#!/usr/bin/env python
# -*- coding: utf-8 -*-

from TowngasBilling import app

# prevent execution when this module is imported by others
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
