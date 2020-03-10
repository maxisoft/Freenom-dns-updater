class DnsRecordBaseException(Exception):
    def __init__(self, msgs, record, old_record_list,*args, **kwargs):
        super(DnsRecordBaseException, self).__init__(*args, **kwargs)
        self._msgs = msgs
        self._record = record
        self._old_record_list = old_record_list

    def __str__(self):
        return "%s(msgs=%s, record=%s, old_record_list=%s)" % (
            type(self).__name__,
            self.msgs,
            self.record,
            self.old_record_list
        )

    @property
    def msgs(self):
        return self._msgs

    @property
    def record(self):
        return self._record

    @property
    def old_record_list(self):
        return self._old_record_list
