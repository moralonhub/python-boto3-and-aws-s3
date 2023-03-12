import boto3
import uuid

from botocore.exceptions import ClientError


def create_bucket_name(bucket_prefix):
    '''
    :param bucket_prefix:
    :return bucket name String:
    '''
    # The generated bucket name must be between 3 and 63 chars long
    return ''.join([bucket_prefix, str(uuid.uuid4())])


def create_bucket(bucket_prefix, s3_connection):
    '''
    :param bucket_prefix:
    :param s3_connection:
    :return bucket_name, bucket_response Tuple:
    '''
    session = boto3.session.Session()
    current_region = session.region_name
    bucket_name = create_bucket_name(bucket_prefix)
    try:
        bucket_response = s3_connection.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': current_region})
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print('Bucket already exists')
    except Exception as e:
        print('An unexpected error occurred:', e)

    print(bucket_name, current_region)
    return bucket_name, bucket_response


def create_temp_file(size, file_name, file_content):
    '''
    :param size:
    :param file_name:
    :param file_content:
    :return file Name String:
    '''
    random_file_name = ''.join([str(uuid.uuid4().hex[:6]), file_name])
    try:
        with open(random_file_name, 'w') as f:
            f.write(str(file_content) * size)
    except IOError:
        print('An error occurred while writing to the file.')
    except Exception as e:
        print('An unexpected error occurred:', e)
    return random_file_name


def copy_to_bucket(bucket_from_name, bucket_to_name, file_name):
    '''
    :param bucket_from_name:
    :param bucket_to_name:
    :param file_name:
    :return:
    '''
    copy_source = {
        'Bucket': bucket_from_name,
        'Key': file_name
    }
    try:
        s3_resource.Object(bucket_to_name, file_name).copy(copy_source)
    except Exception as e:
        print('An unexpected error occurred:', e)


def enable_bucket_versioning(bucket_name):
    '''
    :param bucket_name:
    :return:
    '''
    try:
        bkt_versioning = s3_resource.BucketVersioning(bucket_name)
        bkt_versioning.enable()
    except Exception as e:
        print('An unexpected error occurred:', e)
    print(bkt_versioning.status)


def delete_all_objects(bucket_name):
    '''
    :param bucket_name:
    :return:
    '''
    res = []
    try:
        bucket = s3_resource.Bucket(bucket_name)
        for obj_version in bucket.object_versions.all():
            res.append({'Key': obj_version.object_key,
                        'VersionId': obj_version.id})
        print(res)
        bucket.delete_objects(Delete={'Objects': res})
    except Exception as e:
        print('An unexpected error occurred:', e)


if __name__ == "__main__":
    boto3.setup_default_session(profile_name='johnbryce')
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')

    first_bucket_name, first_response = create_bucket(
        bucket_prefix='firstpythonbucket',
        s3_connection=s3_resource.meta.client)

    second_bucket_name, second_response = create_bucket(
        bucket_prefix='secondpythonbucket',
        s3_connection=s3_resource)

    first_file_name = create_temp_file(300, 'firstfile.txt', 'f')

    first_bucket = s3_resource.Bucket(name=first_bucket_name)
    first_object = s3_resource.Object(bucket_name=first_bucket_name, key=first_file_name)

    first_object_again = first_bucket.Object(first_file_name)
    first_bucket_again = first_object.Bucket()

    first_object.upload_file(first_file_name)

    s3_resource.Object(first_bucket_name, first_file_name).download_file(f'/tmp/{first_file_name}')

    copy_to_bucket(first_bucket_name, second_bucket_name, first_file_name)

    s3_resource.Object(second_bucket_name, first_file_name).delete()

    second_file_name = create_temp_file(400, 'secondfile.txt', 's')
    second_object = s3_resource.Object(first_bucket.name, second_file_name)
    second_object.upload_file(second_file_name, ExtraArgs={
        'ACL': 'public-read'})

    second_object_acl = second_object.Acl()

    print(second_object_acl.grants)

    response = second_object_acl.put(ACL='private')
    second_object_acl.grants

    print(second_object_acl.grants)

    third_file_name = create_temp_file(300, 'thirdfile.txt', 't')
    third_object = s3_resource.Object(first_bucket_name, third_file_name)
    third_object.upload_file(third_file_name, ExtraArgs={
        'ServerSideEncryption': 'AES256'})

    print(third_object.server_side_encryption)

    third_object.upload_file(third_file_name, ExtraArgs={
        'ServerSideEncryption': 'AES256',
        'StorageClass': 'STANDARD_IA'})

    third_object.reload()

    print(third_object.storage_class)

    enable_bucket_versioning(first_bucket_name)

    s3_resource.Object(first_bucket_name, first_file_name).upload_file(
        first_file_name)
    s3_resource.Object(first_bucket_name, first_file_name).upload_file(
        third_file_name)

    s3_resource.Object(first_bucket_name, second_file_name).upload_file(
        second_file_name)

    print(s3_resource.Object(first_bucket_name, first_file_name).version_id)

    for bucket in s3_resource.buckets.all():
        print(bucket.name)

    for bucket_dict in s3_resource.meta.client.list_buckets().get('Buckets'):
        print(bucket_dict['Name'])

    for obj in first_bucket.objects.all():
        print(obj.key)

    for obj in first_bucket.objects.all():
        subsrc = obj.Object()

    print(obj.key, obj.storage_class, obj.last_modified, subsrc.version_id, subsrc.metadata)

    delete_all_objects(first_bucket_name)

    s3_resource.Object(second_bucket_name, first_file_name).upload_file(
        first_file_name)
    delete_all_objects(second_bucket_name)

    s3_resource.Bucket(first_bucket_name).delete()
    s3_resource.meta.client.delete_bucket(Bucket=second_bucket_name)
