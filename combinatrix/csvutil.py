import codecs, csv, io


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and re-encodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = f

    def __iter__(self):
        return self

    def __next__(self):
        val = next(self.reader)
        raw = val.encode("utf-8")
        if raw.startswith(codecs.BOM_UTF8):
            raw = raw.replace(codecs.BOM_UTF8, '', 1)
        return raw


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def __next__(self):
        row = next(self.reader)
        return [str(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = io.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        encoded_row = []
        for s in row:
            if s is None:
                s = ''
            if not isinstance(s, str):
                s = str(s)
            encoded_row.append(s.encode("utf-8"))
        self.writer.writerow(encoded_row)
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


class UnicodeDictReader:
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.reader = UnicodeReader(f, dialect=dialect, encoding=encoding, **kwds)
        self.headers = next(self.reader)

    def __next__(self):
        row = next(self.reader)
        d = {}
        for i in range(len(self.headers)):
            h = self.headers[i]
            v = row[i]
            d[h] = v
        return d

    def __iter__(self):
        return self
