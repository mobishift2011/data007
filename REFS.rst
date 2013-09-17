CASSANDRA
---------
detialed tutorial
http://developer24hours.blogspot.com/2013/01/setting-up-cassandra-multi-nodes-on.html

performance metrics
http://www.slideshare.net/davegardnerisme/running-cassandra-on-amazon-ec2

*datastax tutorial - we use this*
http://www.datastax.com/documentation/cassandra/2.0/webhelp/#cassandra/install/installAMI.html

- install java7::

    add-apt-repository ppa:webupd8team/java
    apt-get update && sudo apt-get install oracle-jdk7-installer
    update-alternatives --set java /usr/lib/jvm/java-7-oracle/jre/bin/java 

- edit ``/etc/casssandra/cassandra-env.sh``
    minimum stack size: 180k -> 256k

- edit ``/etc/cassandra/cassandra.yaml``
    list_address
    snicth
    seeds
    ...

data modeling best practices
http://www.ebaytechblog.com/2012/07/16/cassandra-data-modeling-best-practices-part-1/
http://www.ebaytechblog.com/2012/08/14/cassandra-data-modeling-best-practices-part-2/

HADOOP
------
why ec2 over emc
http://www.semantikoz.com/blog/hadoop-cluster-cost-amazon-ec2-vs-emr/

cloudera manager in ec2
http://blog.cloudera.com/blog/2013/03/how-to-create-a-cdh-cluster-on-amazon-ec2-via-cloudera-manager/
http://www.cloudera.com/content/cloudera-content/cloudera-docs/CM4Ent/latest/Cloudera-Manager-Installation-Guide/cmig_install_on_EC2.html

*install hadoop cluster on ec2 - we go this way*
http://frommyworkshop.blogspot.com/2012/07/single-node-hadoop-cassandra-pig-setup.html
http://www.slideshare.net/benjaminwootton/configuring-your-first-hadoop-cluster-on-ec2

use python in hadoop
http://blog.cloudera.com/blog/2013/01/a-guide-to-python-frameworks-for-hadoop/

METRICS
-------

cassandra bench: 

    infrastructure:

        - m1.large x3
        - Instance Store RAID0 400G x2
        - durable_writes=False
        - replication_factor=2

    benchmark:

        - insert item x3,000,000
        - bandwidth: 20Mbps - 30Mbps
        - tps: 4000-5000
        - size: 689.6MB


