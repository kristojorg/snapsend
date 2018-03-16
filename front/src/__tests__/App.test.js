import React from 'react';
import ReactDOM from 'react-dom';
import App from '../App';
import AppBar from '../AppBar';
import Button from '../Button';
import renderer from 'react-test-renderer';

describe('App Component', () => {
  it('renders without crashing', () => {
    const div = document.createElement('div');
    ReactDOM.render(<App />, div);
    ReactDOM.unmountComponentAtNode(div);
  });
});

describe('Button Component', () => {
  it('Button renders correctly', () => {
    const tree = renderer.create(<Button>Click me!</Button>).toJSON();
    expect(tree).toMatchSnapshot();
  });
  it('Button renders without crashing', () => {
    const div = document.createElement('div');
    ReactDOM.render(<Button>Click me!</Button>, div);
    ReactDOM.unmountComponentAtNode(div);
  });
});

describe('AppBar', () => {
  it('AppBar renders correctly', () => {
    const tree = renderer.create(<AppBar />).toJSON();
    expect(tree).toMatchSnapshot();
  });
  it('AppBar renders without crashing', () => {
    const div = document.createElement('div');
    ReactDOM.render(<AppBar />, div);
    ReactDOM.unmountComponentAtNode(div);
  });
});
