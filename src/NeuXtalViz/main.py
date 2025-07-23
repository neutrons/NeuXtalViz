import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "frontend",
        choices=["qt", "trame"],
        help="The frontend in which to display the application.",
    )
    # This just matches the Trame --server argument.
    parser.add_argument("--server", action="store_true")
    parser.set_defaults(server=False)

    args = parser.parse_args()

    match args.frontend:
        case "qt":
            from NeuXtalViz.qt.gui import gui

            gui()
        case "trame":
            from NeuXtalViz.trame.gui import trame

            trame(open_browser=not args.server)


if __name__ == "__main__":
    main()
