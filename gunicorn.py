def pre_request(worker, req):
    worker.log.debug("%s %s" % (req.method, req.path))
    worker.log.debug("Headers: %s" % (req.headers))
