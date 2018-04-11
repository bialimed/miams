# MIAmS: Microsatellites Instability by AMplicon Sequencing


## Description

Workflow for detecting microsatellite instability by next-generation sequencing
on amplicons.


## Intallation
### 1. Download code
Use one of the following:

* [user way] Downloads the latest released versions from `https://bitbucket.org/miams/downloads/?tab=tags`.
* [developper way] Clones the repository from the latest unreleased version: `git clone --recursive https://bitbucket.org/miams.git`.

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
Configure resources used by the workflow in `application.properties`.

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
    CombinePairs.batch_options = -V -l h_vmem=2G -l mem=2G -q normal
    BamAreasToFastq.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
    BAMIndex.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
    BWAmem.batch_options = -V -l h_vmem=10G -l mem=10G -q normal
    Cutadapt.batch_options = -V -l h_vmem=5G -l mem=5G -q normal
    MSINGS.batch_options = -V -l h_vmem=10G -l mem=10G -q normal
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


## Workflow management
### Launch
The following command is the example used in installation test:

    ${APP_DIR}/envs/miniconda3/bin/source activate MIAmS
    ${APP_DIR}/jflow/bin/jflow_cli.py miamstag \
      --R1 ${APP_DIR}/test/data/instable/I17G01612_S13_L001_R1.fastq.gz \
      --R2 ${APP_DIR}/test/data/instable/I17G01612_S13_L001_R2.fastq.gz \
      --R1 ${APP_DIR}/test/data/stable/I17G01744_S19_L001_R1.fastq.gz \
      --R2 ${APP_DIR}/test/data/stable/I17G01744_S19_L001_R2.fastq.gz \
      --targets ${APP_DIR}/test/data/msi.bed \
      --genome-seq ${APP_DIR}/test/out_detection/Homo_sapiens.GRCh37.75.dna.chromosome.14.fa \
      --intervals ${APP_DIR}/test/data/msi_intervals.tsv \
      --baseline ${APP_DIR}/test/data/MSI_BASELINE.tsv \
      --output-dir ${APP_DIR}/test/out_detection
    ${APP_DIR}/envs/miniconda3/bin/source deactivate

Use `${APP_DIR}/jflow/bin/jflow_bin.py miamstag --help` for more information about
parameters.

### Monitor
#### For monitoring all workflows

    ${APP_DIR}/app/bin/jflow_admin.py status

This command has the following output:

    ID      NAME    STATUS  ELAPSED_TIME    START_TIME      END_TIME
    000002  adivar  completed       0:14:30 Tue Sep 26 13:55:15 2017        Tue Sep 26 14:09:46 2017
    000001  adivar  completed       0:11:02 Mon Sep 25 13:39:31 2017        Mon Sep 25 13:50:34 2017

In this example two workflows has been processed and completed without errors.

#### For monitoring a specific workflow

Use the following command:

    ${APP_DIR}/jflow/bin/jflow_manager.py status \
      --workflow-id <YOUR_WF_ID> \
      --errors

The first block of the output indicate the status and the elapsed time of the
workflow.

    Workflow #000001 (adivar) is failed, time elapsed: 0:02:16 (from Wed Dec 13 16:23:52 2017 to Wed Dec 13 16:26:09 2017)
    Workflow Error :
      File "/work/fescudie/test/adivar/ext/jflow/src/weaver/engine.py", line 156, in execute
        Failed to execute DAG /work/fescudie/jflow/ADIVaR_dev/work/adivar/wf000001/.working/317c6658db/Makeflow using /home/fescudie/cctools/bin/makeflow:
        Command '['/home/fescudie/cctools/bin/makeflow', 'Makeflow', '--log-verbose', '-J', '100', '-T', 'sge']' returned non-zero exit status 1

The second block details the status and the elapsed time of each components of
the workflow. "Total" represents the number of commands defined by the component:
a components can be composed of several commands executed on several input files.

    Components Status :
      - FilterVCF.default, time elapsed 06 (total:2, waiting:0, running:0, failed:2, aborted:0, completed:0)
      - FilterVCFOnAnnot.default, time elapsed 03 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - BAMIndex.libB, time elapsed 06 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - Coverage.libA, time elapsed 09 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - Cutadapt.R2, time elapsed 55 (total:4, waiting:0, running:0, failed:0, aborted:0, completed:4)
      - DepthsDistribution.libB, time elapsed 07 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - AmpliVariantCalling.libA, time elapsed 59 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - Cutadapt.R1, time elapsed 52 (total:4, waiting:0, running:0, failed:0, aborted:0, completed:4)
      - BWAmem.default, time elapsed 01:56 (total:4, waiting:0, running:0, failed:0, aborted:0, completed:4)
      - Coverage.libB, time elapsed 10 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - VCFToTSV.default, time elapsed 00 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:0)
      - VariantsCtrlCheck.default, time elapsed 00 (total:1, waiting:0, running:0, failed:0, aborted:0, completed:0)
      - AmpliVariantCalling.libB, time elapsed 39 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - BAMIndex.default, time elapsed 13 (total:4, waiting:0, running:0, failed:0, aborted:0, completed:4)
      - BAMIndex.libA, time elapsed 06 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - SortVCF.default, time elapsed 06 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - MergeVCFAmpli.default, time elapsed 06 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - AddAmpliRG.libA, time elapsed 11 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - FilterVCFOnCount.default, time elapsed 06 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - AddAmpliRG.libB, time elapsed 11 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - DepthsDistribution.libA, time elapsed 05 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - VEP.default, time elapsed 45 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)
      - ReadsStat.default, time elapsed 01:20 (total:8, waiting:0, running:0, failed:0, aborted:0, completed:8)
      - FilterVCFAnnotOnRNA.default, time elapsed 06 (total:2, waiting:0, running:0, failed:0, aborted:0, completed:2)

The third block details the commands where an execution error has been detected
(the number of command correspond to the total number of failed in second block).
You can see the content of the .stderr file to see the error message.

    Failed Commands :
      - FilterVCF.default :
        /work/fescudie/jflow/ADIVaR_dev/work/adivar/wf000001/.working/317c6658db/_Stash/0/0/0/w000002A /work/fescudie/jflow/ADIVaR_dev/work/adivar/wf000001/FilterVCFAnnotOnRNA_default/17T033348_S3_L001_R1_001_trim.vcf /work/fescudie/jflow/ADIVaR_dev/work/adivar/wf000001/FilterVCF_default/17T033348_S3_L001_R1_001_trim.vcf /work/fescudie/jflow/ADIVaR_dev/work/adivar/wf000001/FilterVCF_default/17T033348_S3_L001_R1_001_trim.stderr
        /work/fescudie/jflow/ADIVaR_dev/work/adivar/wf000001/.working/317c6658db/_Stash/0/0/0/w000002A /work/fescudie/jflow/ADIVaR_dev/work/adivar/wf000001/FilterVCFAnnotOnRNA_default/HORIZON_S1_L001_R1_001_trim.vcf /work/fescudie/jflow/ADIVaR_dev/work/adivar/wf000001/FilterVCF_default/HORIZON_S1_L001_R1_001_trim.vcf /work/fescudie/jflow/ADIVaR_dev/work/adivar/wf000001/FilterVCF_default/HORIZON_S1_L001_R1_001_trim.stderr

### Rerun
You can rerun failed/incomplete steps with the following command:

    ${APP_DIR}/envs/miniconda3/bin/source activate MIAmS
    ${APP_DIR}/jflow/bin/jflow_manager.py rerun \
      --workflow-id <YOUR_WF_ID>
    ${APP_DIR}/envs/miniconda3/bin/source deactivate


## License


## Copyright


## Authors
* Charles Van Goethem
* Frédéric Escudié Laboratoire d'Anatomo-Cytopathologie de l'Institut
Universitaire du Cancer Toulouse - Oncopole


## Contact
escudie.frederic@iuct-oncopole.fr
