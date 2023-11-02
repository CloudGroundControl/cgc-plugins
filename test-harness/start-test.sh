#!/bin/bash

TEST_HARNESS_CONTAINER=australia-southeast1-docker.pkg.dev/cloud-ground-control/plugin-apps/test-harness:0.0.2
# TEST_HARNESS_CONTAINER=test-harness:latest
WEB_UI_CONTAINER=australia-southeast1-docker.pkg.dev/cloud-ground-control/plugin-apps/web-ui:0.0.4
# WEB_UI_CONTAINER=web-ui:latest

trapHandler() {
	echo " - Killing docker containers and exiting"
	docker kill test-harness web-ui plugin > /dev/null 2>&1
	exit 1
}

if [ $# \> 1 ];
then 
	docker kill test-harness web-ui plugin > /dev/null 2>&1
	docker pull $TEST_HARNESS_CONTAINER
	docker pull $WEB_UI_CONTAINER
	trap trapHandler INT ERR

	baseCommand='sudo docker run -d --rm --name test-harness -v "$HOST_SHARE_PATH":/plug-in "$TEST_HARNESS_CONTAINER" /test-harness-core test --working /plug-in --host_folder "$HOST_SHARE_PATH"'
	webUiCommand='sudo docker run -d --rm --name web-ui -v "$HOST_SHARE_PATH"/"$currentFolder":/public/current -p 3001:3000 "$WEB_UI_CONTAINER"'
	pluginCommand='sudo docker run -it --rm --name plugin --gpus all -v "$HOST_SHARE_PATH":/plug-in "$PLUG_IN_CONTAINER" ./start-app.sh $startAppParams'

	PLUG_IN_CONTAINER=$1

	HOST_SHARE_PATH=$2
	if [ ! -d "$HOST_SHARE_PATH" ]; then
		echo "Creating host share path: $HOST_SHARE_PATH"
		sudo mkdir -p $HOST_SHARE_PATH
		sudo chmod 777 $HOST_SHARE_PATH
	else
		echo "Clearing host share path: $HOST_SHARE_PATH"
		sudo rm -rf $HOST_SHARE_PATH/*
	fi


	if [ $# \> 2 ];
	then 
		HOST_TEST_REQUEST=$3
		cp $3 $HOST_SHARE_PATH/host_test_request.json
		baseCommand+=' --in /plug-in/host_test_request.json'
	fi;

	if [ $# \> 3 ];
	then
		VIDEO_FILE=$4
		cp $4 $HOST_SHARE_PATH/source.mp4
		baseCommand+=' --video_source /plug-in/source.mp4'
	fi;

	if [ $# \> 4 ];
	then
		WAY_POINT=$5
		cp $5 $HOST_SHARE_PATH/host_way_point.json
		baseCommand+=' --way_point /plug-in/host_way_point.json'
	fi;

	eval " $baseCommand" > /dev/null
	echo ""
	docker attach test-harness > $HOST_SHARE_PATH/test-harness.log 2>&1 &

	until [ -f $HOST_SHARE_PATH/startCommand.txt ]
	do 
		sleep 1
		echo "Waiting for start command..."
	done

	echo ""
	startAppParams=$(cat $HOST_SHARE_PATH/startCommand.txt)
	echo "Start app params: $startAppParams"

	until [ -f $HOST_SHARE_PATH/currentFolder.txt ]
	do 
		sleep 1
		echo "Waiting for current folder..."
	done

	currentFolder=$(cat $HOST_SHARE_PATH/currentFolder.txt)
	echo "Current folder: $currentFolder"

	eval " $webUiCommand" > /dev/null
	docker attach web-ui > $HOST_SHARE_PATH/web-ui.log 2>&1 &
	
	echo ""
	eval " $pluginCommand"

else
	echo 'Usage:'
	echo './start-test.sh <plugin image> <shared docker volume mount - absolute path> [test request file] [video file] [way point file]'
fi;
