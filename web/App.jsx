import React from 'react';

class Folders extends React.Component {
	render(){
		const directories = this.props.list.map((name, index) => {
						return (
							<div className="w3-card w3-padding-small w3-round folder" key={name}>
								<i className="fa fa-folder"></i>
								{name}
							</div>
							);
					})

		return (
				<div className="folder">
					{directories}
				</div>
				);
	}
}

class App extends React.Component {
	constructor() {
		super();
		this.state = {
			'Folder': ['Blink', 'Armageddon'],
			'File': [],
		};
	}

	render() {
		return (
				<div className="main">
					<Folders list={this.state.Folder} />
					Hohoh
			 	</div>
				);
	}
}

export default App;
