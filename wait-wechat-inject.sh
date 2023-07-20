str=${SERVER_HOST}
server=(${str//:/ }
while true; do
    nc -z ${server}
    if [[ 0 -eq $(echo $?) ]]; then
        echo "wechat-inject"
        break
    fi
    echo "waiting ${server} up"
    sleep 2
done
