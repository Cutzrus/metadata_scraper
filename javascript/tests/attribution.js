    var oTestCase = new YAHOO.tool.TestCase({
    
        name: "TestCase Name",
        
        //---------------------------------------------
        // Setup and tear down
        //---------------------------------------------
        
        setUp : function () {
            this.data = { name : "Nicholas", age : 28 };
        },
    
        tearDown : function () {
            delete this.data;
        },

        //---------------------------------------------
        // Tests
        //---------------------------------------------

        testName: function () {
            YAHOO.util.Assert.areEqual("Nicholas", this.data.name, "Name should be 'Nicholas'");
        },
    
        testAge: function () {
            YAHOO.util.Assert.areEqual(28, this.data.age, "Age should be 28");
        }    
    });

// add the test case to the test suite
YAHOO.cc.test.suite.add(oTestCase);