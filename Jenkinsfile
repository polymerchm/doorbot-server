node {
    def app
    def branch_tag
    def project_uuid = UUID.randomUUID().toString()

    stage('Fetch') {
        checkout scm
    }

    stage('Build') {
        slackSend(
            color: 'good',
            message: "Started build of doorbot server [build #${env.BUILD_NUMBER}, branch ${env.BRANCH_NAME}] (<${env.BUILD_URL}|Open>)"
        )

        try {
            app = docker.build( "doorbot" )

            app.inside {
                // Build config file
                sh 'rm -f config.yml'

                withCredentials([
                    string(
                        credentialsId: 'rfid-dev-db-password'
                        ,variable: 'RFID_DB_PASSWORD'
                    )
                ]) {
                    def example_conf = 'config.yml.example'
                    def conf = readYaml file: example_conf

                    conf.postgresql.passwd = RFID_DB_PASSWORD
                    conf.postgresql.username = 'doorbot'
                    conf.postgresql.database = 'doorbot-' + project_uuid
                    conf.build_id = env.BUILD_ID
                    conf.build_branch = env.BRANCH_NAME
                    conf.build_date = env.BUILD_TIMESTAMP

                    writeYaml file: 'config.yml', data: conf
                }
            }
        }
        catch( err ) {
            slackSend(
                color: '#ff0000',
                message: "Failed build of doorbot server during Build stage [build #${env.BUILD_NUMBER}, branch ${env.BRANCH_NAME}] (<${env.BUILD_URL}|Open>)"
            )
            throw err
        }
    }

    stage( 'Test' ) {
        try {
            app.inside {
                dir( "t" ) {
                    sh 'PYTHONPATH=./:../:${PYTHONPATH} python3 -m nose2'
                }
            }
        }
        catch( err ) {
            discordMsg( "Failed during Test step; ${env.BUILD_ID} on ${env.BRANCH_NAME} (${env.BUILD_URL})" )
            slackSend(
                color: '#ff0000',
                message: "Failed build of doorbot server during Test stage [build #${env.BUILD_NUMBER}, branch ${env.BRANCH_NAME}] (<${env.BUILD_URL}|Open>)"
            )
            throw err
        }
    }
}
