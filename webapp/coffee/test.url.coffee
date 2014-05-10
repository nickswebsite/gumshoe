describe "Url", () ->
  it "should parse a fully qualified url properly", () ->
    url = new Url("http://www.google.com/hello/world?q1=qv1&q2=qv2")
    expect( url.scheme ).toEqual( "http" )
    expect( url.host ).toEqual( "www.google.com" )
    #expect( url.port ).toEqual( null )
    expect( url.path ).toEqual( "/hello/world" )
    #expect( url.params.param1 ).toEqual( "value1" )
    #expect( url.params.param2 ).toEqual( "value2" )
    expect( url.query.q1 ).toEqual( "qv1" )
    expect( url.query.q2 ).toEqual( "qv2" )

