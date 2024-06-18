import os
import yaml
import argparse
from randomize_infrastructure import generate_infrastructure
from randomize_application import generate_with_n_components

def save_as_yaml(data, filename, directory):
    with open(os.path.join(directory, filename), 'w') as file:
        yaml.dump(data, file)


def main(from_n,n, dir,step):
    directories = ['cmp', 'infr']

    directories = [os.path.join(dir, d) for d in directories]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    for i in range(from_n,n,step):
        for directory in directories:
            data = generate_infrastructure(i) if directory==directories[1] else  generate_with_n_components(i)
            filename = f"{i}.yaml"
            save_as_yaml(data, filename, directory)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate test files.')
    parser.add_argument('from_n', type=int, help='from number of node and component.')
    parser.add_argument('step', type=int, help='step number between n.')
    parser.add_argument('n', type=int, help='The number of files to generate.')
    parser.add_argument('dir', type=str, help='root directory where output')
    args = parser.parse_args()

    main(args.from_n,args.n, args.dir,args.step)
