# MIAmS: Microsatellites Instability by AMplicon Sequencing


## Description

Workflow for detecting microsatellite instability by next-generation sequencing
on amplicons.


## Intallation
### 1. Download code
Use one of the following:

* [user way] Downloads the latest released versions from `https://bitbucket.org/toulousemontpellier/miams/downloads/?tab=tags`.
* [developper way] Clones the repository from the latest unreleased version: `git clone --recursive https://bitbucket.org/toulousemontpellier/miams.git`.

The application folder has the following structure:

    <APP_DIR>/
    ├── install/                        # Scripts for install the application
    ├── jflow/
    │   ├── bin/                        # Scripts for workflows management (run, rerun, monitor)
    │   ├── ...
    │   └── application.properties.tpl  # Application configuration file
    ├── README.md
    └── test/                           # Scripts and data to test the workflows

### 2. Configure application
Configure resources used by the workflow in `jflow/application.properties.tpl`.

All the detail on configuration options can be find in `app/docs/jflow_advanced_configuration.html`.

    [global]
    # uncomment and set if not in the PATH, should be version >= 4.4.3
    #makeflow = ###APP_FOLDER###/envs/miniconda3/envs/###APP_ENV_NAME###/bin/makeflow
    # batch system type: local, condor, sge, moab, cluster, wq, hadoop, mpi-queue
    batch_system_type = sge
    # add these options to all batch submit files
    batch_options =
    # add these options to limit the number of jobs sumitted in parallel
    limit_submission = 100
    # on which socket host should run the web server
    server_socket_host = 127.0.0.1
    # on which socket port should run the web server
    server_socket_port = 8080
    # date format
    date_format = %d/%m/%Y

In this example Makeflow is accessible in PATH, the scheduler system used is
[SGE](https://arc.liv.ac.uk/trac/SGE/) and the graphical interface will be
accessible on `localhost:8080` if you run the jflow server.

    [email]
    # if you want an email to be sent at the end of the workflow execution
    # set the smtp_server and the from_address values
    smtp_server =
    smtp_port =
    from_address =
    from_password =
    # uncomment and set if you want to use these values for all the workflow
    # these variables can be overloaded within the workflow implementation by
    # using self.set_to_address("address"), self.set_subject("subject"),
    # self.set_message("message") functions
    #to_address =
    #subject =
    #message =

This section is used to send mails at the end of a workflow execution. In this
example no mail are sended.

    [storage]
    # In this section, ###USER### (if it's used) is replaced by $USER environment variable.
    # where should be written the log file
    log_file = ###USER###/work/MIAmS/jflow.log
    # Where should the pipelines write results, should be accessible
    # by all cluster nodes
    work_directory = ###USER###/work/MIAmS/work
    # Where should the pipelines write temporary files, should be
    # accessible by all cluster nodes
    tmp_directory = ###USER###/work/MIAmS/tmp
    browse_root_dir = ###USER###

These folders are used to store intermediate files.

    # Set cluster parameters of some components
    [components]
    BamAreasToFastq.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
    BAMIndex.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
    BWAmem.batch_options = -V -l h_vmem=10G -l mem=10G -q normal
    CombinePairs.batch_options = -V -l h_vmem=2G -l mem=2G -q normal
    CreateMSIRef.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
    Cutadapt.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
    GatherLocusRes.batch_options = -V -l h_vmem=3G -l mem=3G -q normal
    MIAmSClassify.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
    MSINGS.batch_options = -V -l h_vmem=10G -l mem=10G -q normal
    MSINGSBaseline.batch_options = -V -l h_vmem=10G -l mem=10G -q normal
    MSIMergeReports.batch_options = -V -l h_vmem=3G -l mem=3G -q normal

Ressources booked by each component of the workflow. If your *batch system type*
is **local** these options are not necessary.

The parameters show components properties:

* The components use the same environment as the main job (*-V*).
* The maximum virtual memory (*-l h_vmem=XG*) and the memory used by a component.
* On SGE the queue can control priority, limit execution time and ressources.
(*-q X*).

### 3. Launch installer

    ${APP_DIR}/install/install_app.sh

This command:

* creates a virtual environment for the application
* installs dependencies on this environment
* writes the final configuration (jflow/application.properties) from your template
* checks the installation by running workflows on a small dataset

## Prepare analysis
MIAmS is mainly based on [mSINGS](https://bitbucket.org/uwlabmed/msings). This
software works in 3 steps:

* Convert a BED describing loci to an interval format.
* Learn from many stable samples the standard distribution of InDel size by loci.
This step create a model used in following analyses.
* Find MSI status by comparison between InDel profile in sample and InDel
profile in model.

The two first steps described below should be proceed once contrary to to the
third described in *Workflows management* that must be processed for each analysis.

### Convert BED to interval

    ${APP_DIR}/envs/msings/scripts/create_intervals.py \
      --input-bed ${APP_DIR}/test/data/msi.bed \
      --output ${APP_DIR}/test/out_model/msi_intervals.tsv

### Build MSI reference with *MIAmS Learn*
The following command must be used on large number of stable and instable samples
coming from your laboratory. Take in mind the sentence of mSINGS's authors:
"_Baseline statistics vary markedly from assay-to-assay and lab-to-lab. It is
CRITICAL that you prepare a baseline file that is specific for your analytic
process, and for which data have been generated using the same protocols._"

    source ${APP_DIR}/envs/miniconda3/bin/activate MIAmS
    ${APP_DIR}/jflow/bin/jflow_cli.py miamslearn \
      --R1 ${APP_DIR}/test/data/stable/I17G01744_S19_L001_R1.fastq.gz \
      --R2 ${APP_DIR}/test/data/stable/I17G01744_S19_L001_R2.fastq.gz \
      --R1 ${APP_DIR}/test/data/instable/I17G01612_S13_L001_R1.fastq.gz \
      --R2 ${APP_DIR}/test/data/instable/I17G01612_S13_L001_R2.fastq.gz \
      --annotations ${APP_DIR}/test/data/loci_annot.tsv \
      --targets ${APP_DIR}/test/data/msi.bed \
      --genome-seq ${APP_DIR}/test/bank/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa \
      --intervals ${APP_DIR}/test/data/msi_intervals.tsv \
      --output-baseline ${APP_DIR}/test/out_model/baseline.tsv \
      --output-training ${APP_DIR}/test/out_model/models.json \
      --output-log ${APP_DIR}/test/out_model/baseline_log.txt
    source ${APP_DIR}/envs/miniconda3/bin/deactivate

The annotations file describe the status of all loci in all samples in TSV
format.

    sample	locus_position	method_id	key	value	type
    splA	1:102-500	model	status	MSS
    splA	1:9005-9105	model	status	Undetermined
    splB	1:102-500	model	status	MSI
    splB	1:9005-9105	model	status	MSI

One row correspond to one locus in one sample and contains:

* The sample name.
* The locus position.
* The name of the method storing information. In reference creation we use `model`.
* The name used to index the annotation. In reference creation we add the MSI `status`.
* The value for the annotation. In reference creation `MSS` or `MSI` or `Undetermined`.
* The type of value.


## Workflows management
### Launch
The following command is the example used in installation test:

    source ${APP_DIR}/envs/miniconda3/bin/activate MIAmS
    ${APP_DIR}/jflow/bin/jflow_cli.py miamstag \
      --R1 ${APP_DIR}/test/data/instable/I17G01612_S13_L001_R1.fastq.gz \
      --R2 ${APP_DIR}/test/data/instable/I17G01612_S13_L001_R2.fastq.gz \
      --R1 ${APP_DIR}/test/data/stable/I17G01744_S19_L001_R1.fastq.gz \
      --R2 ${APP_DIR}/test/data/stable/I17G01744_S19_L001_R2.fastq.gz \
      --models ${APP_DIR}/test/data/models.json \
      --targets ${APP_DIR}/test/data/msi.bed \
      --genome-seq ${APP_DIR}/test/bank/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa \
      --intervals ${APP_DIR}/test/data/msi_intervals.tsv \
      --baseline ${APP_DIR}/test/data/MSI_BASELINE.tsv \
      --output-dir ${APP_DIR}/test/out_detection
    source ${APP_DIR}/envs/miniconda3/bin/deactivate

Use `${APP_DIR}/jflow/bin/jflow_bin.py miamstag --help` for more information about
parameters.

### Monitor
#### For monitoring all workflows

    ${APP_DIR}/jflow/bin/jflow_admin.py status

This command has the following output:

    ID      NAME    STATUS  ELAPSED_TIME    START_TIME      END_TIME
    000003  miamstag        failed          0:01:03 Thu Apr 12 11:24:02 2018        Thu Apr 12 11:25:05 2018
    000002  miamstag        completed       0:01:13 Thu Apr 12 11:11:54 2018        Thu Apr 12 11:13:08 2018
    000001  miamstag        completed       0:01:04 Wed Apr 11 17:28:41 2018        Wed Apr 11 17:29:45 2018

In this example the workflows 1 and 2 have been processed and completed with
success the workflow 3 has failed.

#### For monitoring a specific workflow

Use the following command:

    ${APP_DIR}/jflow/bin/jflow_admin.py status \
      --workflow-id ${YOUR_WF_ID} \
      --errors

The first block of the output indicate the status and the elapsed time of the
workflow.

    Workflow #000003 (miamstag) is failed, time elapsed: 0:01:03 (from Thu Apr 12 11:24:02 2018 to Thu Apr 12 11:25:05 2018)
    Workflow Error :
      File "/work/fescudie/MIAmS/test2/msings_workflow/jflow/src/weaver/engine.py", line 156, in execute
        Failed to execute DAG /work/fescudie/jflow/MIAmS/work/miamstag/wf000003/.working/78f9a76eb0/Makeflow using /work/fescudie/MIAmS/test2/msings_workflow/envs/miniconda3/envs/MIAmS/bin/makeflow:
        Command '['/work/fescudie/MIAmS/test2/msings_workflow/envs/miniconda3/envs/MIAmS/bin/makeflow', 'Makeflow', '--log-verbose', '-J', '100', '-T', 'sge']' returned non-zero exit status 1

The second block details the status and the elapsed time of each components of
the workflow. "Total" represents the number of commands defined by the component:
a components can be composed of several commands executed on several input files.

    Components Status :
      - MSIMergeReports.default, time elapsed 08 (total:2, waiting:0, running:0, failed:2, aborted:0, completed:0)
      - BAMIndex.default, time elapsed 05 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - BamAreasToFastq.default, time elapsed 18 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - MSINGS.default, time elapsed 16 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - BWAmem.default, time elapsed 27 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - CombinePairs.default, time elapsed 01:01 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)

The third block details the commands where an execution error has been detected
(the number of command correspond to the total number of failed in second block).
You can see the content of the .stderr file to see the error message.

    Failed Commands :
      - MSIMergeReports.default :
        /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/.working/78f9a76eb0/_Stash/0/0/0/w000000A /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/MSINGS_default/I17G01612_S13_L001_report.txt /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/MSIMergeReports_default/spl_0_comb_reports_list.tsv /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/MSIMergeReports_default/I17G01612_S13_L001_report_report.json /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/MSIMergeReports_default/I17G01612_S13_L001_report.stderr
        /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/.working/78f9a76eb0/_Stash/0/0/0/w000000A /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/MSINGS_default/I17G01744_S19_L001_report.txt /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/MSIMergeReports_default/spl_1_comb_reports_list.tsv /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/MSIMergeReports_default/I17G01744_S19_L001_report_report.json /work/fescudie/jflow/MIAmS/work/miamstag/wf000004/MSIMergeReports_default/I17G01744_S19_L001_report.stderr

### Rerun
You can rerun failed/incomplete steps with the following command:

    source ${APP_DIR}/envs/miniconda3/bin/activate MIAmS
    ${APP_DIR}/jflow/bin/jflow_admin.py rerun \
      --workflow-id ${YOUR_WF_ID}
    source ${APP_DIR}/envs/miniconda3/bin/deactivate


## License


## Copyright


## Authors
* Charles Van Goethem Laboratoire de Biologie des Tumeurs Solides Hôpital Arnaud
de Villeneuve CHU de Montpellier
* Frédéric Escudié Laboratoire d'Anatomo-Cytopathologie de l'Institut
Universitaire du Cancer Toulouse - Oncopole


## Contact
escudie.frederic@iuct-oncopole.fr
