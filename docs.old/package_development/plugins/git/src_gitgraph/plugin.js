// Global configuration

var gitGraph = new GitGraph({
  template: "metro", // "blackarrow" or "metro" or Template Object
  //template: "blackarrow", // "blackarrow" or "metro" or Template Object
  //orientation: "horizontal", 
  //mode: "compact" // Special compact mode : hide messages & compact graph
}); 


// Prepare files on the master branch
var master = gitGraph.branch("master"); // Create branch named "master"
master.commit({"message" : "Initial commit with README.md, CHANGELOG, .gitignore",
               "author" : "Fritz <fritz@foo.com>"})
      .commit({"message" : "A little update on README.md",
               "author" : "Fritz <fritz@foo.com>"});
    
// Switch on the develop branch
var develop = gitGraph.branch("develop"); // Create branch named "develop" from "master"
    
// Work on the develop branch
develop.commit({"message" : "Create info.json file",
                "author" : "Fritz <fritz@foo.com>"});
develop.commit({"message" : "Create python file",
                "author" : "Fritz <fritz@foo.com>"}); 
develop.commit({"message" : "Add documentation",
                "author" : "Fritz <fritz@foo.com>"}); 
develop.commit({"message" : "A lot of other upgrades!!!",
                "author" : "Fritz <fritz@foo.com>"}); 
develop.commit({"message" : "Version 1.0 is ready",
                "author" : "Fritz <fritz@foo.com>"}); 
develop.commit({"message" : "Tag 1.0",
                "author" : "Fritz <fritz@foo.com>",
                "dotStrokeWidth" : 10,
                "dotColor" : "white"}); 

// Release a first version
master.checkout(); // Checkout on master branch
develop.merge(master, {"message" : "Merge tag 1.0 into master",
                       "author" : "Fritz <fritz@foo.com>"}); 

develop.commit({"message" : "Start working on the next release",
                "author" : "Fritz <fritz@foo.com>"});
develop.commit({"message" : "Finish working on the next release",
                "author" : "Fritz <fritz@foo.com>"});
develop.commit({"message" : "Tag 2.0",
                "author" : "Fritz <fritz@foo.com>",
                "dotStrokeWidth" : 10,
                "dotColor" : "white"});

// Release a second version
master.checkout(); // Checkout on master branch
develop.merge(master, {"message" : "Merge tag 2.0 into master",
                       "author" : "Fritz <fritz@foo.com>"});

develop.commit({"message" : "Fix a bug",
                "author" : "Fritz <fritz@foo.com>"});
develop.commit({"message" : "Tag 2.1 (bugfix version)",
                "author" : "Fritz <fritz@foo.com>",
                "dotStrokeWidth" : 10,
                "dotColor" : "white"});

// Release a bugfix version
master.checkout(); // Checkout on master branch
develop.merge(master, {"message" : "Merge tag 2.1 into master",
                       "author" : "Fritz <fritz@foo.com>"});

develop.commit({"message" : "Start working on the next version",
                "author" : "Fritz <fritz@foo.com>"});

