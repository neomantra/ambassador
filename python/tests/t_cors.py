# Note that there's also a CORS OptionTest in t_optiontests.py.

from kat.harness import Query

from abstract_tests import AmbassadorTest, HTTP, Node, ServiceType


class GlobalCORSTest(AmbassadorTest):
    target: ServiceType

    def init(self):
        self.target = HTTP()

    def config(self):
        yield self, self.format("""
---
apiVersion: ambassador/v1
kind:  Module
name:  ambassador
config:
  cors:
    origins: http://foo.example.com
    methods: POST, GET, OPTIONS
---
apiVersion: ambassador/v1
kind:  Mapping
name:  {self.target.path.k8s}-foo
prefix: /foo/
service: {self.target.path.fqdn}
---
apiVersion: ambassador/v1
kind:  Mapping
name:  {self.target.path.k8s}-bar
prefix: /bar/
service: {self.target.path.fqdn}
cors:
  origins: http://bar.example.com
  methods: POST, GET, OPTIONS
---
apiVersion: ambassador/v1
kind:  Mapping
name:  {self.target.path.k8s}-baz
prefix: /baz/
service: {self.target.path.fqdn}
cors:
  regex_origins: 'http://*.baz.example.com,http://baz\\d+.example.com'
  methods: POST, GET, OPTIONS
""")

    def queries(self):
        # 0. No Access-Control-Allow-Origin because no Origin was provided.
        yield Query(self.url("foo/"))

        # 1. Access-Control-Allow-Origin because a matching Origin was provided.
        yield Query(self.url("foo/"), headers={ "Origin": "http://foo.example.com" })

        # 2. No Access-Control-Allow-Origin because the provided Origin does not match.
        yield Query(self.url("foo/"), headers={ "Origin": "http://wrong.example.com" })

        # 3. No Access-Control-Allow-Origin because no Origin was provided.
        yield Query(self.url("bar/"))

        # 4. Access-Control-Allow-Origin because a matching Origin was provided.
        yield Query(self.url("bar/"), headers={ "Origin": "http://bar.example.com" })

        # 5. No Access-Control-Allow-Origin because the provided Origin does not match.
        yield Query(self.url("bar/"), headers={ "Origin": "http://wrong.example.com" })

        # 6. No Access-Control-Allow-Origin because no Origin was provided.
        yield Query(self.url("baz/"))

        # 7. No Access-Control-Allow-Origin because the provided Origin does not match.
        yield Query(self.url("baz/"), headers={ "Origin": "http://wrong.example.com" })

        # 8. No Access-Control-Allow-Origin because the provided Origin does not match.
        yield Query(self.url("baz/"), headers={ "Origin": "http://baz.example.com" })

        # 9. Access-Control-Allow-Origin because a matching Origin was provided.
        yield Query(self.url("baz/"), headers={ "Origin": "http://a1.baz.example.com" })

        # 10. Access-Control-Allow-Origin because a matching Origin was provided.
        yield Query(self.url("baz/"), headers={ "Origin": "http://baz123.example.com" })

    def check(self):
        assert self.results[0].backend.name == self.target.path.k8s
        assert "Access-Control-Allow-Origin" not in self.results[0].headers

        assert self.results[1].backend.name == self.target.path.k8s
        assert self.results[1].headers["Access-Control-Allow-Origin"] == [ "http://foo.example.com" ]

        assert self.results[2].backend.name == self.target.path.k8s
        assert "Access-Control-Allow-Origin" not in self.results[2].headers

        assert self.results[3].backend.name == self.target.path.k8s
        assert "Access-Control-Allow-Origin" not in self.results[3].headers

        assert self.results[4].backend.name == self.target.path.k8s
        assert self.results[4].headers["Access-Control-Allow-Origin"] == [ "http://bar.example.com" ]

        assert self.results[5].backend.name == self.target.path.k8s
        assert "Access-Control-Allow-Origin" not in self.results[5].headers

        assert self.results[6].backend.name == self.target.path.k8s
        assert "Access-Control-Allow-Origin" not in self.results[6].headers

        assert self.results[7].backend.name == self.target.path.k8s
        assert "Access-Control-Allow-Origin" not in self.results[7].headers

        assert self.results[8].backend.name == self.target.path.k8s
        assert "Access-Control-Allow-Origin" not in self.results[8].headers

        assert self.results[9].backend.name == self.target.path.k8s
        assert self.results[9].headers["Access-Control-Allow-Origin"] == [ "http://a1.baz.example.com" ]

        assert self.results[10].backend.name == self.target.path.k8s
        assert self.results[10].headers["Access-Control-Allow-Origin"] == [ "http://baz123.example.com" ]
