# creates a folder in the current directory and downloads pics and csv into it.
# need to fix last loop so very last entry doesn't generate error

import flickrapi
import wgetter
import time
import io
import os


api_key = ''
secret = ''
flickr = flickrapi.FlickrAPI(api_key, secret, format='parsed-json')


os.system('clear')
group_url = raw_input("Enter a Flickr Group URL: ")
group_id = group_url.strip('/').split('/')[-1]
print " "
print "Files will be saved in folder " + group_id
time.sleep(1)
print "Retrieving ID's. Please wait."
group_pool_photos = []

page = 1
perpage = 300
success = True


# create folder if nec
if not os.path.exists(group_id):
    os.makedirs(group_id)

with io.FileIO(group_id + "/" + "list.csv", "w") as file:
    while True:
        response = flickr.groups.pools.getPhotos(group_id=group_id, page=page, perpage=perpage)
        if response['stat'] != 'ok':
            print 'Error occurred in flickr.groups.pools.getPhotos'
            print(response)
            success = False
            break

        if len(response['photos']['photo']) == 0:
            break

        group_pool_photos.extend(response['photos']['photo'])
        page += 1

    if success:
        print 'Photos: {}'.format(len(group_pool_photos))
        time.sleep(1)
        print 'Downloading now.'
        print " "
        file.write('PICID, PICURL, TAKEN, LOCATION, REALNAME, TITLE, DESCRIPTION, PATH_ALIAS')
        file.write('\r\n')
        for line in group_pool_photos:
            photoinfo = flickr.photos.getInfo(photo_id=line['id'])
            description = (photoinfo['photo']['description']['_content']).replace(",", "").encode("utf-8")
            if not description:
                description = 'na'
            taken = photoinfo['photo']['dates']['taken']
            path_alias = photoinfo['photo']['owner']['path_alias']
            if not path_alias:
                path_alias = 'na'
            title = photoinfo['photo']['title']['_content'].replace(";", "").replace(",", "").encode("utf-8")
            location = photoinfo['photo']['owner']['location'].replace(";", "").replace(",", "").encode("utf-8")
            realname = photoinfo['photo']['owner']['realname'].replace(";", "").replace(",", "").replace('   ', ' ').replace('  ', ' ').replace('  ', ' ').encode("utf-8")
            picsize = flickr.photos.getSizes(photo_id=line['id'])
            picurl = (picsize['sizes']['size'][-1]['source'])
            file.write(line['id'] + "," + picurl + "," + taken + "," + location + "," + realname + "," + title + "," + description + "," + path_alias)
            file.write('\r\n')
            filename = wgetter.download(picurl, outdir=group_id)
            time.sleep(0.5)
